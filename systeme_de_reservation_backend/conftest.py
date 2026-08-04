"""Fixtures partagées entre apps — utilisées par les nouveaux tests ajoutés
lors de l'audit/renforcement de la suite. Les tests existants gardent leurs
propres helpers locaux (`make_membre_client`, etc.) : pas de refactor global,
pour ne pas toucher à des tests qui passent déjà.
"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from apps.identite.tests.factories import GestionnaireFactory, MembreFactory


@pytest.fixture
def membre_client(db):
    """Retourne `(APIClient authentifié, Membre)` pour un nouveau membre."""

    def _make():
        membre = MembreFactory()
        client = APIClient()
        client.force_authenticate(user=membre.utilisateur)
        return client, membre

    return _make


@pytest.fixture
def gestionnaire_client(db):
    """Retourne `(APIClient authentifié, Gestionnaire)` pour un nouveau gestionnaire."""

    def _make():
        gestionnaire = GestionnaireFactory()
        client = APIClient()
        client.force_authenticate(user=gestionnaire.utilisateur)
        return client, gestionnaire

    return _make
