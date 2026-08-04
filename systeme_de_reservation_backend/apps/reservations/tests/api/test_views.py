"""Tests d'API (APIClient DRF) — nécessitent une base PostgreSQL réelle."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.identite.models import Gestionnaire, Membre, Utilisateur
from apps.reservations.infrastructure.models import CreneauSlot
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel

pytestmark = pytest.mark.django_db


def make_espace(disponible: bool = True) -> EspaceCoworkingModel:
    return EspaceCoworkingModel.objects.create(
        nom=f'Salle {uuid.uuid4()}',
        type_espace=EspaceCoworkingModel.TypeEspace.SALLE_REUNION,
        capacite=8,
        tarif_horaire=Decimal('20.00'),
        disponible=disponible,
        id_gestionnaire=uuid.uuid4(),
    )


def make_creneau(espace, jour=date(2026, 8, 1), debut=time(9, 0), fin=time(11, 0)) -> CreneauSlot:
    return CreneauSlot.objects.create(espace=espace, date=jour, heure_debut=debut, heure_fin=fin)


def make_membre_client() -> tuple[APIClient, Membre]:
    utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    membre = Membre.objects.create(utilisateur=utilisateur)
    client = APIClient()
    client.force_authenticate(user=utilisateur)
    return client, membre


def make_gestionnaire_client() -> tuple[APIClient, Gestionnaire]:
    utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    gestionnaire = Gestionnaire.objects.create(utilisateur=utilisateur)
    client = APIClient()
    client.force_authenticate(user=utilisateur)
    return client, gestionnaire


class TestCreerReservation:
    def test_creation_reussie_201(self):
        espace = make_espace()
        creneau = make_creneau(espace)
        client, _ = make_membre_client()

        response = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')

        assert response.status_code == 201, response.data
        assert response.data['statut'] == 'EN_ATTENTE'
        assert response.data['acompte'] == '40.00'
        assert ReservationModel.objects.count() == 1

    def test_creneau_deja_reserve_409(self):
        espace = make_espace()
        creneau = make_creneau(espace)
        client_a, _ = make_membre_client()
        client_b, _ = make_membre_client()
        client_a.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')

        response = client_b.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')

        assert response.status_code == 409

    def test_salle_inactive_400(self):
        espace = make_espace(disponible=False)
        creneau = make_creneau(espace)
        client, _ = make_membre_client()

        response = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')

        assert response.status_code == 400

    def test_creneau_introuvable_404(self):
        client, _ = make_membre_client()
        response = client.post('/api/v2/reservations/', data={'creneau': str(uuid.uuid4())}, format='json')
        assert response.status_code == 404

    def test_non_authentifie_401(self):
        espace = make_espace()
        creneau = make_creneau(espace)
        response = APIClient().post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        assert response.status_code == 401


def _reserver_et_payer(client, creneau, django_capture_on_commit_callbacks):
    """Le paiement mock déclenche la confirmation via `transaction.on_commit` +
    le dispatcher in-process : sous pytest-django (transactions non commitées),
    il faut capter et rejouer ces callbacks explicitement."""
    creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
    reservation_id = creation.data['id']
    with django_capture_on_commit_callbacks(execute=True):
        client.post(
            '/api/v2/paiements/',
            data={'reservation': reservation_id, 'montant': '40.00', 'moyen': 'CARTE'},
            format='json',
        )
    return reservation_id


class TestAnnulerReservation:
    def test_annulation_par_le_proprietaire_200(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = make_creneau(espace)
        client, _ = make_membre_client()
        reservation_id = _reserver_et_payer(client, creneau, django_capture_on_commit_callbacks)

        response = client.patch(f'/api/v2/reservations/{reservation_id}/', data={}, format='json')

        assert response.status_code == 200, response.data
        assert response.data['statut'] == 'ANNULEE'
        assert CreneauSlot.objects.get(pk=creneau.id).statut == CreneauSlot.Statut.DISPONIBLE

    def test_annulation_par_non_proprietaire_403(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = make_creneau(espace)
        client, _ = make_membre_client()
        reservation_id = _reserver_et_payer(client, creneau, django_capture_on_commit_callbacks)

        autre_client, _ = make_membre_client()
        response = autre_client.patch(f'/api/v2/reservations/{reservation_id}/', data={}, format='json')

        assert response.status_code == 403

    def test_annulation_reservation_en_attente_409(self):
        """Non payée -> encore EN_ATTENTE -> ne peut pas être annulée par le membre (cf. CH2 v2)."""
        espace = make_espace()
        creneau = make_creneau(espace)
        client, _ = make_membre_client()
        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')

        response = client.patch(f'/api/v2/reservations/{creation.data["id"]}/', data={}, format='json')

        assert response.status_code == 409

    def test_annulation_reservation_introuvable_404(self):
        client, _ = make_membre_client()
        response = client.patch(f'/api/v2/reservations/{uuid.uuid4()}/', data={}, format='json')
        assert response.status_code == 404


class TestListerReservations:
    def test_liste_filtree_par_membre(self):
        espace = make_espace()
        client, _ = make_membre_client()
        client.post('/api/v2/reservations/', data={'creneau': str(make_creneau(espace).id)}, format='json')

        autre_client, _ = make_membre_client()
        autre_client.post(
            '/api/v2/reservations/',
            data={'creneau': str(make_creneau(espace, debut=time(14, 0), fin=time(16, 0)).id)},
            format='json',
        )

        response = client.get('/api/v2/reservations/')

        assert response.status_code == 200
        assert len(response.data) == 1


class TestSallesDisponibles:
    def test_liste_salles_disponibles(self):
        espace = make_espace()
        response = APIClient().get(
            '/api/v2/salles/disponibles/',
            data={'date': '2026-08-01', 'heure_debut': '09:00:00', 'heure_fin': '11:00:00'},
        )
        assert response.status_code == 200
        assert len(response.data) == 1
        assert response.data[0]['id'] == str(espace.id_espace)


class TestSalleViewSetPermissions:
    def test_membre_peut_lister(self):
        make_espace()
        client, _ = make_membre_client()
        response = client.get('/api/v2/salles/')
        assert response.status_code == 200

    def test_membre_ne_peut_pas_creer_403(self):
        client, _ = make_membre_client()
        response = client.post(
            '/api/v2/salles/',
            data={
                'nom': 'Nouvelle salle',
                'type_espace': 'OPEN_SPACE',
                'capacite': 4,
                'tarif_horaire': '15.00',
                'id_gestionnaire': str(uuid.uuid4()),
            },
            format='json',
        )
        assert response.status_code == 403

    def test_gestionnaire_peut_creer_201(self):
        client, _ = make_gestionnaire_client()
        response = client.post(
            '/api/v2/salles/',
            data={
                'nom': 'Nouvelle salle',
                'type_espace': 'OPEN_SPACE',
                'capacite': 4,
                'tarif_horaire': '15.00',
                'id_gestionnaire': str(uuid.uuid4()),
            },
            format='json',
        )
        assert response.status_code == 201, response.data
