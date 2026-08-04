"""Parcours bout-en-bout : réserver -> payer -> auto-confirmation / libération.

Le mock de paiement déclenche `PaiementValide`/`PaiementEchoue` via
`transaction.on_commit` : sous pytest-django (transactions non commitées en
temps normal), on capte et rejoue ces callbacks avec
`django_capture_on_commit_callbacks`.
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.identite.models import Membre, Utilisateur
from apps.paiements.gateway import MockPaymentGateway
from apps.paiements.models import Paiement
from apps.paiements.services import InitierPaiementUseCase
from apps.reservations.infrastructure.models import CreneauSlot
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel

pytestmark = pytest.mark.django_db


class GatewayRefusant(MockPaymentGateway):
    def traiter(self, montant, devise, moyen) -> bool:
        return False


def make_espace() -> EspaceCoworkingModel:
    return EspaceCoworkingModel.objects.create(
        nom=f'Salle {uuid.uuid4()}',
        type_espace=EspaceCoworkingModel.TypeEspace.SALLE_REUNION,
        capacite=8,
        tarif_horaire=Decimal('20.00'),
        disponible=True,
        id_gestionnaire=uuid.uuid4(),
    )


def make_membre_client():
    utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    membre = Membre.objects.create(utilisateur=utilisateur)
    client = APIClient()
    client.force_authenticate(user=utilisateur)
    return client, membre


class TestParcoursPaiementReussi:
    def test_paiement_accepte_confirme_la_reservation(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0))
        client, _ = make_membre_client()

        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        reservation_id = creation.data['id']

        with django_capture_on_commit_callbacks(execute=True):
            response = client.post(
                '/api/v2/paiements/',
                data={'reservation': reservation_id, 'montant': '40.00', 'moyen': 'CARTE'},
                format='json',
            )

        assert response.status_code == 201
        assert response.data['statut'] == 'ACCEPTE'

        reservation = ReservationModel.objects.get(pk=reservation_id)
        assert reservation.statut == ReservationModel.Statut.CONFIRMEE
        assert CreneauSlot.objects.get(pk=creneau.id).statut == CreneauSlot.Statut.RESERVE


class TestParcoursPaiementEchoue:
    def test_paiement_refuse_libere_le_creneau(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0))
        reservation_model = ReservationModel.objects.create(
            creneau_slot=creneau,
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=Membre.objects.create(utilisateur=Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local')),
        )
        creneau.statut = CreneauSlot.Statut.RESERVE
        creneau.save(update_fields=['statut'])

        with django_capture_on_commit_callbacks(execute=True):
            InitierPaiementUseCase(gateway=GatewayRefusant()).execute(
                reservation_id=reservation_model.id_reservation,
                montant=Decimal('40.00'),
                devise='TND',
                moyen=Paiement.Moyen.CARTE,
            )

        reservation_model.refresh_from_db()
        assert reservation_model.statut == ReservationModel.Statut.ANNULEE
        assert CreneauSlot.objects.get(pk=creneau.id).statut == CreneauSlot.Statut.DISPONIBLE


class TestPaiementImmutable:
    def test_paiement_refuse_deuxieme_tentative_409(self):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0))
        client, _ = make_membre_client()
        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        reservation_id = creation.data['id']

        client.post(
            '/api/v2/paiements/',
            data={'reservation': reservation_id, 'montant': '40.00', 'moyen': 'CARTE'},
            format='json',
        )
        response = client.post(
            '/api/v2/paiements/',
            data={'reservation': reservation_id, 'montant': '40.00', 'moyen': 'CARTE'},
            format='json',
        )
        assert response.status_code == 409

    def test_pas_de_put_patch_delete(self):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0))
        client, _ = make_membre_client()
        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        paiement = client.post(
            '/api/v2/paiements/',
            data={'reservation': creation.data['id'], 'montant': '40.00', 'moyen': 'CARTE'},
            format='json',
        )
        paiement_id = paiement.data['id']

        assert client.put(f'/api/v2/paiements/{paiement_id}/', data={}, format='json').status_code == 405
        assert client.patch(f'/api/v2/paiements/{paiement_id}/', data={}, format='json').status_code == 405
        assert client.delete(f'/api/v2/paiements/{paiement_id}/').status_code == 405
