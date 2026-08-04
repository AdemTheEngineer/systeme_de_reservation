import uuid
from datetime import timedelta

import pytest
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken

from apps.identite.models import Gestionnaire, Membre, Utilisateur

pytestmark = pytest.mark.django_db


def make_utilisateur(password: str = 'motdepasse123') -> Utilisateur:
    return Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password=password)


class TestLogin:
    def test_login_reussi_200(self):
        utilisateur = make_utilisateur('secret123')
        response = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )
        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_mauvais_mot_de_passe_401(self):
        utilisateur = make_utilisateur('secret123')
        response = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'mauvais'}, format='json'
        )
        assert response.status_code == 401


class TestRefreshEtLogout:
    def test_refresh_renouvelle_l_access_token(self):
        utilisateur = make_utilisateur('secret123')
        login = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )
        refresh_response = APIClient().post(
            '/api/v2/auth/refresh/', data={'refresh': login.data['refresh']}, format='json'
        )
        assert refresh_response.status_code == 200
        assert 'access' in refresh_response.data

    def test_logout_blackliste_le_refresh(self):
        utilisateur = make_utilisateur('secret123')
        login = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )
        refresh = login.data['refresh']

        client = APIClient()
        client.force_authenticate(user=utilisateur)
        logout_response = client.post('/api/v2/auth/logout/', data={'refresh': refresh}, format='json')
        assert logout_response.status_code == 204

        # Le refresh blacklisté ne peut plus être utilisé pour rafraîchir.
        reuse_response = APIClient().post('/api/v2/auth/refresh/', data={'refresh': refresh}, format='json')
        assert reuse_response.status_code == 401

    def test_refresh_invalide_401(self):
        response = APIClient().post('/api/v2/auth/refresh/', data={'refresh': 'invalide'}, format='json')
        assert response.status_code == 401


class TestMe:
    def test_me_membre(self):
        utilisateur = make_utilisateur()
        Membre.objects.create(utilisateur=utilisateur)
        client = APIClient()
        client.force_authenticate(user=utilisateur)

        response = client.get('/api/v2/auth/me/')
        assert response.status_code == 200
        assert response.data['role'] == 'membre'

    def test_me_non_authentifie_401(self):
        response = APIClient().get('/api/v2/auth/me/')
        assert response.status_code == 401


class TestValiditeDesTokens:
    def test_access_token_valide_donne_acces_200(self):
        utilisateur = make_utilisateur('secret123')
        Membre.objects.create(utilisateur=utilisateur)
        login = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["access"]}')
        assert client.get('/api/v2/auth/me/').status_code == 200

    def test_access_token_expire_401(self):
        utilisateur = make_utilisateur()
        Membre.objects.create(utilisateur=utilisateur)
        token = AccessToken.for_user(utilisateur)
        token.set_exp(lifetime=-timedelta(minutes=1))

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        assert client.get('/api/v2/auth/me/').status_code == 401

    def test_access_token_forge_401(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer pas.un.jwt')
        assert client.get('/api/v2/auth/me/').status_code == 401

    def test_refresh_utilise_comme_access_401(self):
        """Un refresh token n'est pas un access token : le type est vérifié."""
        utilisateur = make_utilisateur('secret123')
        Membre.objects.create(utilisateur=utilisateur)
        login = APIClient().post(
            '/api/v2/auth/login/', data={'email': utilisateur.email, 'mot_de_passe': 'secret123'}, format='json'
        )

        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {login.data["refresh"]}')
        assert client.get('/api/v2/auth/me/').status_code == 401


class TestPermissionsMembresViewSet:
    def test_membre_ne_peut_pas_lister_403(self):
        utilisateur = make_utilisateur()
        Membre.objects.create(utilisateur=utilisateur)
        client = APIClient()
        client.force_authenticate(user=utilisateur)

        response = client.get('/api/v2/membres/')
        assert response.status_code == 403

    def test_gestionnaire_peut_lister_200(self):
        utilisateur = make_utilisateur()
        Gestionnaire.objects.create(utilisateur=utilisateur)
        client = APIClient()
        client.force_authenticate(user=utilisateur)

        response = client.get('/api/v2/membres/')
        assert response.status_code == 200
