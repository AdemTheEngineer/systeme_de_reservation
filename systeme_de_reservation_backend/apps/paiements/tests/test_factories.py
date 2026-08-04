"""Tests de non-régression des factories partagées.

Régression couverte : `PaiementFactory` déclarait `_valeur`/`_devise` comme
attributs de classe — factory_boy ignore silencieusement les attributs
préfixés `_`, donc `montant_valeur` partait à NULL en base (IntegrityError).
Corrigé via `Meta.rename`.
"""

from decimal import Decimal

import pytest

from apps.identite.tests.factories import GestionnaireFactory, MembreFactory
from apps.paiements.models import Paiement
from apps.paiements.tests.factories import PaiementFactory
from apps.reservations.tests.factories import (
    CreneauSlotFactory,
    EspaceCoworkingFactory,
    ReservationModelFactory,
)

pytestmark = pytest.mark.django_db


def test_paiement_factory_persiste_le_montant():
    membre = MembreFactory()
    reservation = ReservationModelFactory(membre=membre)

    paiement = PaiementFactory(reservation=reservation)

    recharge = Paiement.objects.get(pk=paiement.id)
    assert recharge._valeur == Decimal('40.00')
    assert recharge._devise == 'TND'
    assert recharge.statut == Paiement.Statut.ACCEPTE


def test_paiement_factory_accepte_des_valeurs_explicites():
    reservation = ReservationModelFactory(membre=MembreFactory())

    paiement = PaiementFactory(reservation=reservation, valeur=Decimal('99.50'), devise='EUR')

    recharge = Paiement.objects.get(pk=paiement.id)
    assert recharge._valeur == Decimal('99.50')
    assert recharge._devise == 'EUR'


def test_chaine_complete_des_factories():
    """Smoke test : toute la chaîne membre → espace → créneau → réservation
    → paiement se construit sans violer de contrainte en base."""
    membre = MembreFactory()
    gestionnaire = GestionnaireFactory()
    assert membre.utilisateur.check_password('motdepasse123')
    assert gestionnaire.pk is not None

    espace = EspaceCoworkingFactory()
    creneau = CreneauSlotFactory(espace=espace)
    reservation = ReservationModelFactory(creneau_slot=creneau, membre=membre)
    assert reservation.espace_id == espace.id_espace

    paiement = PaiementFactory(reservation=reservation)
    assert paiement.pk is not None
