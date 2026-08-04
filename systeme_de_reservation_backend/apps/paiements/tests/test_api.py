"""Compléments API paiements : validation du montant, propriété de la
réservation, périmètre de lecture (un membre ne voit que ses paiements).
"""

import uuid
from decimal import Decimal

import pytest

from apps.reservations.tests.factories import CreneauSlotFactory

pytestmark = pytest.mark.django_db


def _reserver(client, creneau) -> str:
    response = client.post('/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json')
    assert response.status_code == 201, response.data
    return response.data['id']


def _payer(client, reservation_id, montant='40.00'):
    return client.post(
        '/api/v2/paiements/',
        data={'reservation': reservation_id, 'montant': montant, 'moyen': 'CARTE'},
        format='json',
    )


class TestValidationMontant:
    def test_montant_nul_400(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        assert _payer(client, reservation_id, montant='0.00').status_code == 400

    def test_montant_negatif_400(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        assert _payer(client, reservation_id, montant='-40.00').status_code == 400

    def test_montant_different_de_l_acompte_409(self, membre_client):
        """L'acompte dû est 2h × 20 = 40.00 : payer un autre montant est refusé."""
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        response = _payer(client, reservation_id, montant='39.99')
        assert response.status_code == 409

    def test_reservation_introuvable_membre_403(self, membre_client):
        """Pour un membre, la vérification de propriété passe avant celle
        d'existence : une réservation inconnue donne 403 (pas de fuite
        d'information sur l'existence), le 404 est réservé au gestionnaire."""
        client, _ = membre_client()
        assert _payer(client, str(uuid.uuid4())).status_code == 403

    def test_reservation_introuvable_gestionnaire_404(self, gestionnaire_client):
        client, _ = gestionnaire_client()
        assert _payer(client, str(uuid.uuid4())).status_code == 404


class TestProprieteDuPaiement:
    def test_un_autre_membre_ne_peut_pas_payer_403(self, membre_client):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())

        autre_client, _ = membre_client()
        assert _payer(autre_client, reservation_id).status_code == 403

    def test_liste_scopee_au_membre(self, membre_client, django_capture_on_commit_callbacks):
        client_a, _ = membre_client()
        reservation_a = _reserver(client_a, CreneauSlotFactory())
        with django_capture_on_commit_callbacks(execute=True):
            _payer(client_a, reservation_a)

        client_b, _ = membre_client()
        reservation_b = _reserver(client_b, CreneauSlotFactory())
        with django_capture_on_commit_callbacks(execute=True):
            _payer(client_b, reservation_b)

        response = client_a.get('/api/v2/paiements/')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert str(response.data['results'][0]['reservation']) == reservation_a

    def test_gestionnaire_voit_tous_les_paiements(
        self, membre_client, gestionnaire_client, django_capture_on_commit_callbacks
    ):
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        with django_capture_on_commit_callbacks(execute=True):
            _payer(client, reservation_id)

        client_gestionnaire, _ = gestionnaire_client()
        response = client_gestionnaire.get('/api/v2/paiements/')

        assert response.status_code == 200
        assert response.data['count'] == 1

    def test_detail_d_un_paiement_d_autrui_404(self, membre_client, django_capture_on_commit_callbacks):
        """Le queryset étant scopé au membre, le paiement d'autrui est
        invisible (404, pas de fuite d'information via 403)."""
        client, _ = membre_client()
        reservation_id = _reserver(client, CreneauSlotFactory())
        with django_capture_on_commit_callbacks(execute=True):
            paiement = _payer(client, reservation_id)

        autre_client, _ = membre_client()
        assert autre_client.get(f'/api/v2/paiements/{paiement.data["id"]}/').status_code == 404
