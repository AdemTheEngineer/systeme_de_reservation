"""Tests des endpoints KPI (EF-16 -> EF-18), gestionnaire-only."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.identite.models import Gestionnaire, Membre, Utilisateur
from apps.reservations.infrastructure.models import CreneauSlot
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel

pytestmark = pytest.mark.django_db


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


def make_gestionnaire_client():
    utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    Gestionnaire.objects.create(utilisateur=utilisateur)
    client = APIClient()
    client.force_authenticate(user=utilisateur)
    return client


class TestPermissionsKPI:
    def test_membre_ne_peut_pas_acceder_403(self):
        client, _ = make_membre_client()
        response = client.get('/api/v2/kpis/dashboard/', data={'debut': '2026-08-01', 'fin': '2026-08-31'})
        assert response.status_code == 403

    def test_non_authentifie_401(self):
        response = APIClient().get('/api/v2/kpis/dashboard/', data={'debut': '2026-08-01', 'fin': '2026-08-31'})
        assert response.status_code == 401


class TestTauxOccupation:
    def test_occupation_reflete_une_reservation_confirmee(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(
            espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0)
        )
        client, _ = make_membre_client()
        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                '/api/v2/paiements/',
                data={'reservation': creation.data['id'], 'montant': '40.00', 'moyen': 'CARTE'},
                format='json',
            )

        gestionnaire_client = make_gestionnaire_client()
        response = gestionnaire_client.get(
            '/api/v2/kpis/occupation/', data={'debut': '2026-08-01', 'fin': '2026-08-01'}
        )

        assert response.status_code == 200
        ligne = next(r for r in response.data if r['salle_id'] == str(espace.id_espace))
        assert ligne['heures_reservees'] == '2.00'
        assert ligne['heures_disponibles'] == '24.00'


class TestRevenuEtDashboard:
    def test_revenu_periode_compte_les_paiements_acceptes(self, django_capture_on_commit_callbacks):
        espace = make_espace()
        creneau = CreneauSlot.objects.create(
            espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0)
        )
        client, _ = make_membre_client()
        creation = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
        with django_capture_on_commit_callbacks(execute=True):
            client.post(
                '/api/v2/paiements/',
                data={'reservation': creation.data['id'], 'montant': '40.00', 'moyen': 'CARTE'},
                format='json',
            )

        gestionnaire_client = make_gestionnaire_client()
        # `date_paiement` est horodaté au moment réel du test (auto_now_add),
        # indépendamment de la date d'usage de la salle (2026-08-01) : on
        # couvre une période large pour être sûr d'inclure "maintenant".
        response = gestionnaire_client.get('/api/v2/kpis/revenu/', data={'debut': '2020-01-01', 'fin': '2030-12-31'})

        assert response.status_code == 200
        assert response.data['nombre_reservations'] >= 1
        assert Decimal(response.data['somme_acomptes']) >= Decimal('40.00')

    def test_dashboard_agrege_occupation_et_revenu(self):
        make_espace()
        gestionnaire_client = make_gestionnaire_client()
        response = gestionnaire_client.get(
            '/api/v2/kpis/dashboard/', data={'debut': '2026-08-01', 'fin': '2026-08-31'}
        )
        assert response.status_code == 200
        assert 'occupation' in response.data
        assert 'revenu' in response.data

    def test_fin_avant_debut_400(self):
        gestionnaire_client = make_gestionnaire_client()
        response = gestionnaire_client.get(
            '/api/v2/kpis/dashboard/', data={'debut': '2026-08-31', 'fin': '2026-08-01'}
        )
        assert response.status_code == 400
