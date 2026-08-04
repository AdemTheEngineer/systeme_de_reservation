"""ViewSets DRF — aucune règle métier : parsing → appel du use case →
sérialisation de la réponse → mapping des exceptions vers des codes HTTP.

Note : `confirmer_reservation`/`liberer_creneau` ne sont exposées par
aucune route ici. Le flux nominal (EF-11) est déclenché par les événements
`PaiementValide`/`PaiementEchoue` émis par `apps.paiements`, câblés via le
dispatcher in-process (`apps.core.domain.dispatcher`) — pas via HTTP.
"""

from __future__ import annotations

import uuid

from django.db.models.deletion import ProtectedError, RestrictedError
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.views import exception_handler as drf_exception_handler

from apps.reservations.application.dto import AnnulerReservationInput, CreerReservationInput, ReservationDTO
from apps.reservations.application.exceptions import (
    CreneauIndisponibleError,
    CreneauIntrouvableError,
    ReservationIntrouvableError,
    SalleIntrouvableError,
)
from apps.reservations.application.use_cases.annuler_reservation import AnnulerReservationUseCase
from apps.reservations.application.use_cases.consulter_disponibilites import (
    ListerReservationsUseCase,
    ListerSallesDisponiblesUseCase,
)
from apps.reservations.application.use_cases.kpis import (
    ObtenirDashboardKPIUseCase,
    ObtenirRevenuPeriodeUseCase,
    ObtenirTauxOccupationUseCase,
)
from apps.reservations.application.use_cases.reserver_creneau import ReserverCreneauUseCase
from apps.reservations.domain.exceptions import (
    ChevauchementCreneauError,
    CreneauInvalideError,
    MontantInvalideError,
    SalleInactiveError,
    TransitionInvalideError,
)
from apps.reservations.infrastructure.event_publishers import LoggingEventPublisher
from apps.reservations.infrastructure.models import CreneauSlot, EspaceCoworking
from apps.reservations.infrastructure.repositories import (
    DjangoCreneauSlotRepository,
    DjangoDisponibiliteRepository,
    DjangoKPIRepository,
    DjangoReservationReadRepository,
    DjangoReservationRepository,
    DjangoSalleRepository,
)
from apps.identite.interfaces.api.permissions import EstGestionnaire
from apps.reservations.interfaces.api.permissions import (
    EstGestionnaireOuLectureSeule,
    EstProprietaireDeLaReservation,
)
from apps.reservations.interfaces.api.serializers import (
    CreerReservationSerializer,
    CreneauSerializer,
    DashboardKPISerializer,
    DisponibiliteQuerySerializer,
    PeriodeQuerySerializer,
    ReservationSerializer,
    RevenuPeriodeSerializer,
    SalleDisponibleSerializer,
    SalleSerializer,
    TauxOccupationSerializer,
)


def reservation_exception_handler(exc, context):
    """Mappe les exceptions domaine/application vers des codes HTTP (409/400/404)."""
    response = drf_exception_handler(exc, context)
    if response is not None:
        return response

    if isinstance(exc, (SalleIntrouvableError, ReservationIntrouvableError, CreneauIntrouvableError)):
        return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
    if isinstance(exc, (ChevauchementCreneauError, TransitionInvalideError, CreneauIndisponibleError)):
        return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)
    if isinstance(exc, (CreneauInvalideError, MontantInvalideError, SalleInactiveError)):
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    if isinstance(exc, (ProtectedError, RestrictedError)):
        return Response(
            {'detail': "Suppression impossible : des ressources dépendent encore de cet objet."},
            status=status.HTTP_409_CONFLICT,
        )
    return None


def _uuid_ou_404(valeur: str) -> uuid.UUID:
    try:
        return uuid.UUID(valeur)
    except ValueError as exc:
        raise NotFound("Identifiant invalide.") from exc


class SalleViewSet(viewsets.ModelViewSet):
    """`salles` : lecture pour tout membre authentifié, écriture gestionnaire uniquement."""

    queryset = EspaceCoworking.objects.order_by('nom')
    serializer_class = SalleSerializer
    permission_classes = [IsAuthenticated, EstGestionnaireOuLectureSeule]
    search_fields = ['nom']
    ordering_fields = ['nom', 'capacite', 'tarif_horaire']
    filterset_fields = {'capacite': ['gte']}

    def get_queryset(self):
        queryset = super().get_queryset()
        capacite_min = self.request.query_params.get('capacite_min')
        if capacite_min is not None:
            queryset = queryset.filter(capacite__gte=capacite_min)
        return queryset


class CreneauViewSet(viewsets.ModelViewSet):
    """`creneaux` : CRUD complet, écriture gestionnaire uniquement."""

    queryset = CreneauSlot.objects.select_related('espace').order_by('date', 'heure_debut')
    serializer_class = CreneauSerializer
    permission_classes = [IsAuthenticated, EstGestionnaireOuLectureSeule]
    filterset_fields = ['espace', 'date', 'statut']

    def get_queryset(self):
        queryset = super().get_queryset()
        salle_id = self.request.query_params.get('salle')
        if salle_id:
            queryset = queryset.filter(espace_id=salle_id)
        return queryset


class ReservationViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('partial_update', 'destroy'):
            return [IsAuthenticated(), EstProprietaireDeLaReservation()]
        return [IsAuthenticated()]

    def list(self, request):
        salle_id = request.query_params.get('salle')
        membre = getattr(request.user, 'membre', None)
        est_gestionnaire = hasattr(request.user, 'gestionnaire')
        if membre is None and not est_gestionnaire:
            return Response([])

        try:
            salle_uuid = uuid.UUID(salle_id) if salle_id else None
        except ValueError as exc:
            raise ValidationError({'salle': 'UUID invalide.'}) from exc

        use_case = ListerReservationsUseCase(DjangoReservationReadRepository())
        resultats = use_case.execute(
            membre_id=membre.id if membre else None,
            salle_id=salle_uuid,
        )
        return Response(ReservationSerializer(resultats, many=True).data)

    def retrieve(self, request, pk=None):
        reservation = DjangoReservationRepository().get_by_id(_uuid_ou_404(pk))
        if reservation is None:
            raise NotFound("Réservation introuvable.")
        membre = getattr(request.user, 'membre', None)
        est_gestionnaire = hasattr(request.user, 'gestionnaire')
        if not est_gestionnaire and (membre is None or membre.id != reservation.membre_id):
            raise PermissionDenied("Seul le membre propriétaire ou un gestionnaire peut consulter cette réservation.")
        return Response(ReservationSerializer(ReservationDTO.from_entity(reservation)).data)

    def create(self, request):
        serializer = CreerReservationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        membre = getattr(request.user, 'membre', None)
        if membre is None:
            return Response({'detail': 'Seul un membre peut réserver.'}, status=status.HTTP_403_FORBIDDEN)

        use_case = ReserverCreneauUseCase(
            DjangoSalleRepository(),
            DjangoReservationRepository(),
            DjangoCreneauSlotRepository(),
            LoggingEventPublisher(),
        )
        output = use_case.execute(
            CreerReservationInput(
                creneau_id=serializer.validated_data['creneau'],
                membre_id=membre.id,
            )
        )
        return Response(ReservationSerializer(output.reservation).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        return self._annuler(request, pk)

    def destroy(self, request, pk=None):
        self._annuler(request, pk)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _annuler(self, request, pk):
        reservation_repository = DjangoReservationRepository()
        reservation = reservation_repository.get_by_id(_uuid_ou_404(pk))
        if reservation is None:
            raise NotFound("Réservation introuvable.")
        self.check_object_permissions(request, reservation)

        use_case = AnnulerReservationUseCase(
            reservation_repository, DjangoCreneauSlotRepository(), LoggingEventPublisher()
        )
        output = use_case.execute(AnnulerReservationInput(reservation_id=reservation.id))
        return Response(ReservationSerializer(output.reservation).data)


class SallesDisponiblesView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = DisponibiliteQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)

        use_case = ListerSallesDisponiblesUseCase(DjangoDisponibiliteRepository())
        resultats = use_case.execute(**query.validated_data)
        return Response(SalleDisponibleSerializer(resultats, many=True).data)


class TauxOccupationView(APIView):
    """EF-16, gestionnaire-only."""

    permission_classes = [IsAuthenticated, EstGestionnaire]

    def get(self, request):
        query = PeriodeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        resultats = ObtenirTauxOccupationUseCase(DjangoKPIRepository()).execute(**query.validated_data)
        return Response(TauxOccupationSerializer(resultats, many=True).data)


class RevenuPeriodeView(APIView):
    """EF-17, gestionnaire-only."""

    permission_classes = [IsAuthenticated, EstGestionnaire]

    def get(self, request):
        query = PeriodeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        resultat = ObtenirRevenuPeriodeUseCase(DjangoKPIRepository()).execute(**query.validated_data)
        return Response(RevenuPeriodeSerializer(resultat).data)


class DashboardKPIView(APIView):
    """EF-18, gestionnaire-only."""

    permission_classes = [IsAuthenticated, EstGestionnaire]

    def get(self, request):
        query = PeriodeQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        resultat = ObtenirDashboardKPIUseCase(DjangoKPIRepository()).execute(**query.validated_data)
        return Response(DashboardKPISerializer(resultat).data)
