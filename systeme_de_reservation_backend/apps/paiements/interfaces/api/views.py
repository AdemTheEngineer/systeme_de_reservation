"""`paiements` — GET (liste/détail/statut), POST uniquement. Immutable :
pas de PUT/PATCH/DELETE (cf. `http_method_names`)."""

from __future__ import annotations

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.paiements.exceptions import PaiementImpossibleError, ReservationIntrouvableError
from apps.paiements.models import Paiement
from apps.paiements.services import InitierPaiementUseCase
from apps.paiements.interfaces.api.serializers import PaiementCreateSerializer, PaiementSerializer
from apps.reservations.infrastructure.models import Reservation as ReservationModel


class PaiementViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Lecture/création scopées au membre propriétaire de la réservation liée
    (gestionnaire : accès complet), pour éviter qu'un membre puisse consulter
    ou régler le paiement d'un autre membre."""

    http_method_names = ['get', 'post', 'head', 'options']
    queryset = Paiement.objects.select_related('reservation').order_by('-date_paiement')
    serializer_class = PaiementSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['reservation', 'statut']

    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(self.request.user, 'gestionnaire'):
            return queryset
        membre = getattr(self.request.user, 'membre', None)
        if membre is None:
            return queryset.none()
        return queryset.filter(reservation__membre_id=membre.id)

    def create(self, request, *args, **kwargs):
        serializer = PaiementCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not hasattr(request.user, 'gestionnaire'):
            membre = getattr(request.user, 'membre', None)
            appartient_au_membre = membre is not None and ReservationModel.objects.filter(
                pk=data['reservation'], membre_id=membre.id
            ).exists()
            if not appartient_au_membre:
                return Response(
                    {'detail': "Seul le membre propriétaire de la réservation peut initier ce paiement."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        try:
            paiement = InitierPaiementUseCase().execute(
                reservation_id=data['reservation'],
                montant=data['montant'],
                devise=data['devise'],
                moyen=data['moyen'],
            )
        except ReservationIntrouvableError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_404_NOT_FOUND)
        except PaiementImpossibleError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_409_CONFLICT)

        return Response(PaiementSerializer(paiement).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def statut(self, request, pk=None):
        paiement = self.get_object()
        return Response({'statut': paiement.statut})
