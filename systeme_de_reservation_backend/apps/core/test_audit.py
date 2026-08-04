import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.core.models import AuditLog
from apps.identite.models import Membre, Utilisateur
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


class TestAuditTrigger:
    def test_insertion_reservation_journalisee_avec_acteur_et_ip(self):
        """`force_authenticate` ne pose pas de vrai en-tête `Authorization` :
        le middleware (qui décode le JWT lui-même, cf. apps/core/middleware.py)
        ne verrait rien. On passe donc par un vrai login pour obtenir un
        access token et l'attacher explicitement à la requête."""
        utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='secret123')
        Membre.objects.create(utilisateur=utilisateur)
        client = APIClient()
        login = client.post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')

        espace = make_espace()
        creneau = CreneauSlot.objects.create(
            espace=espace, date=date(2026, 8, 1), heure_debut=time(9, 0), heure_fin=time(11, 0)
        )

        response = client.post(
            '/api/v2/reservations/', data={'creneau': str(creneau.id)}, format='json', REMOTE_ADDR='203.0.113.7'
        )
        assert response.status_code == 201
        reservation_id = response.data['id']

        entree = AuditLog.objects.filter(table_name='reservation', row_id=reservation_id, operation='INSERT').first()
        assert entree is not None
        assert entree.acteur_id == utilisateur.id
        assert entree.ip == '203.0.113.7'
        assert entree.donnees['statut'] == 'EN_ATTENTE'

    def test_operation_sans_authentification_ne_casse_pas_le_middleware(self):
        make_espace()
        response = APIClient().get(
            '/api/v2/salles/disponibles/',
            data={'date': '2026-08-01', 'heure_debut': '09:00:00', 'heure_fin': '11:00:00'},
        )
        assert response.status_code == 200
