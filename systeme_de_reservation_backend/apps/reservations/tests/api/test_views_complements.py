"""Compléments API : détail d'une réservation (propriété), DELETE (annulation),
pagination et filtrage des ressources CRUD (`salles`, `creneaux`).
"""

import uuid
from datetime import date, time

import pytest
from rest_framework.test import APIClient

from apps.reservations.infrastructure.models import CreneauSlot
from apps.reservations.tests.factories import CreneauSlotFactory, EspaceCoworkingFactory

pytestmark = pytest.mark.django_db


def _reserver(client, creneau) -> str:
    response = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
    assert response.status_code == 201, response.data
    return response.data['id']


def _payer(client, reservation_id, django_capture_on_commit_callbacks):
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            '/api/v2/paiements/',
            data={'reservation': reservation_id, 'montant': '40.00', 'moyen': 'CARTE'},
            format='json',
        )
    assert response.status_code == 201, response.data


class TestDetailReservation:
    def test_proprietaire_peut_consulter_200(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())

        response = client.get(f'/api/v2/reservations/{reservation_id}/')

        assert response.status_code == 200
        assert response.data['id'] == reservation_id
        assert response.data['statut'] == 'EN_ATTENTE'

    def test_autre_membre_ne_peut_pas_consulter_403(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())

        autre_client, _ = membre_client()
        response = autre_client.get(f'/api/v2/reservations/{reservation_id}/')

        assert response.status_code == 403

    def test_gestionnaire_peut_consulter_200(self, membre_client, gestionnaire_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())

        client_gestionnaire, _ = gestionnaire_client()
        response = client_gestionnaire.get(f'/api/v2/reservations/{reservation_id}/')

        assert response.status_code == 200

    def test_introuvable_404(self, membre_client):
        client, _ = membre_client()
        assert client.get(f'/api/v2/reservations/{uuid.uuid4()}/').status_code == 404

    def test_identifiant_malforme_404(self, membre_client):
        client, _ = membre_client()
        assert client.get('/api/v2/reservations/pas-un-uuid/').status_code == 404

    def test_non_authentifie_401(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        assert APIClient().get(f'/api/v2/reservations/{reservation_id}/').status_code == 401


class TestSupprimerReservation:
    def test_delete_par_le_proprietaire_204_et_libere_le_creneau(
        self, membre_client, django_capture_on_commit_callbacks
    ):
        creneau = CreneauSlotFactory()
        client, _ = membre_client()
        reservation_id = _reserver(client, creneau)
        _payer(client, reservation_id, django_capture_on_commit_callbacks)

        response = client.delete(f'/api/v2/reservations/{reservation_id}/')

        assert response.status_code == 204
        assert CreneauSlot.objects.get(pk=creneau.id).statut == CreneauSlot.Statut.DISPONIBLE

    def test_delete_par_non_proprietaire_403(self, membre_client, django_capture_on_commit_callbacks):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        _payer(client, reservation_id, django_capture_on_commit_callbacks)

        autre_client, _ = membre_client()
        assert autre_client.delete(f'/api/v2/reservations/{reservation_id}/').status_code == 403


class TestPaginationEtFiltres:
    def test_liste_salles_paginee_a_20(self, membre_client):
        for _ in range(25):
            EspaceCoworkingFactory()
        client, _ = membre_client()

        response = client.get('/api/v2/salles/')

        assert response.status_code == 200
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20
        assert response.data['next'] is not None

        page_2 = client.get('/api/v2/salles/', data={'page': 2})
        assert len(page_2.data['results']) == 5

    def test_filtre_salles_par_capacite_min(self, membre_client):
        EspaceCoworkingFactory(capacite=4)
        grande = EspaceCoworkingFactory(capacite=16)
        client, _ = membre_client()

        response = client.get('/api/v2/salles/', data={'capacite_min': 10})

        assert response.status_code == 200
        assert [r['id_espace'] for r in response.data['results']] == [str(grande.id_espace)]

    def test_recherche_salles_par_nom(self, membre_client):
        EspaceCoworkingFactory(nom='Salle Hannibal')
        EspaceCoworkingFactory(nom='Bureau Ulysse')
        client, _ = membre_client()

        response = client.get('/api/v2/salles/', data={'search': 'Hannibal'})

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['nom'] == 'Salle Hannibal'

    def test_filtre_creneaux_par_statut(self, membre_client):
        espace = EspaceCoworkingFactory()
        CreneauSlotFactory(espace=espace, heure_debut=time(9, 0), heure_fin=time(11, 0))
        reserve = CreneauSlotFactory(
            espace=espace, heure_debut=time(14, 0), heure_fin=time(16, 0), statut=CreneauSlot.Statut.RESERVE
        )
        client, _ = membre_client()

        response = client.get('/api/v2/creneaux/', data={'statut': 'RESERVE'})

        assert response.status_code == 200
        assert [r['id'] for r in response.data['results']] == [str(reserve.id)]

    def test_filtre_creneaux_par_salle(self, membre_client):
        creneau = CreneauSlotFactory()
        CreneauSlotFactory()  # autre salle
        client, _ = membre_client()

        response = client.get('/api/v2/creneaux/', data={'salle': str(creneau.espace_id)})

        assert response.status_code == 200
        assert [r['id'] for r in response.data['results']] == [str(creneau.id)]


class TestEcritureCreneauxGestionnaireSeulement:
    def test_membre_ne_peut_pas_creer_de_creneau_403(self, membre_client):
        espace = EspaceCoworkingFactory()
        client, _ = membre_client()
        response = client.post(
            '/api/v2/creneaux/',
            data={'espace': str(espace.id_espace), 'date': '2026-09-01', 'heure_debut': '09:00', 'heure_fin': '11:00'},
            format='json',
        )
        assert response.status_code == 403

    def test_gestionnaire_peut_creer_un_creneau_201(self, gestionnaire_client):
        espace = EspaceCoworkingFactory()
        client, _ = gestionnaire_client()
        response = client.post(
            '/api/v2/creneaux/',
            data={'espace': str(espace.id_espace), 'date': '2026-09-01', 'heure_debut': '09:00', 'heure_fin': '11:00'},
            format='json',
        )
        assert response.status_code == 201, response.data
