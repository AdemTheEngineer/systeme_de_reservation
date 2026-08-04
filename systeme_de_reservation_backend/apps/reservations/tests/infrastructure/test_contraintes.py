"""Contraintes déclarées en base (CHECK / UNIQUE) — défense en profondeur :
même en contournant le domaine et les serializers, PostgreSQL doit refuser
les états invalides. (La contrainte GIST anti-chevauchement a ses propres
tests dans `test_repositories.py` et `test_concurrence.py`.)
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.identite.tests.factories import MembreFactory
from apps.paiements.models import Paiement
from apps.reservations.infrastructure.models import CreneauSlot, EspaceCoworking
from apps.reservations.infrastructure.models import Reservation as ReservationModel
from apps.reservations.tests.factories import (
    CreneauSlotFactory,
    EspaceCoworkingFactory,
    ReservationModelFactory,
)

pytestmark = pytest.mark.django_db


def _cree_en_atomic(factory_ou_manager, **kwargs):
    with transaction.atomic():
        return factory_ou_manager(**kwargs)


class TestContraintesEspaceCoworking:
    def test_nom_unique(self):
        EspaceCoworkingFactory(nom='Salle Carthage')
        with pytest.raises(IntegrityError):
            _cree_en_atomic(EspaceCoworkingFactory, nom='Salle Carthage')

    def test_capacite_nulle_refusee(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(EspaceCoworkingFactory, capacite=0)

    def test_tarif_horaire_negatif_refuse(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(EspaceCoworkingFactory, tarif_horaire=Decimal('-1.00'))

    def test_type_espace_inconnu_refuse(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(EspaceCoworkingFactory, type_espace='PISCINE')


class TestContraintesCreneau:
    def test_heure_fin_avant_heure_debut_refusee(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(CreneauSlotFactory, heure_debut=time(11, 0), heure_fin=time(9, 0))

    def test_heure_fin_egale_heure_debut_refusee(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(CreneauSlotFactory, heure_debut=time(9, 0), heure_fin=time(9, 0))

    def test_creneau_duplique_sur_meme_salle_refuse(self):
        creneau = CreneauSlotFactory()
        with pytest.raises(IntegrityError):
            _cree_en_atomic(
                CreneauSlotFactory,
                espace=creneau.espace,
                date=creneau.date,
                heure_debut=creneau.heure_debut,
                heure_fin=creneau.heure_fin,
            )


class TestContraintesReservation:
    def test_date_fin_avant_date_debut_refusee(self):
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ReservationModel.objects.create(
                    date_debut='2026-08-01T11:00:00+00:00',
                    date_fin='2026-08-01T09:00:00+00:00',
                    statut=ReservationModel.Statut.EN_ATTENTE,
                    montant_total=Decimal('40.00'),
                    espace=EspaceCoworkingFactory(),
                    membre=MembreFactory(),
                )

    def test_statut_inconnu_refuse(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(ReservationModelFactory, membre=MembreFactory(), statut='BROUILLON')

    def test_montant_total_negatif_refuse(self):
        with pytest.raises(IntegrityError):
            _cree_en_atomic(ReservationModelFactory, membre=MembreFactory(), montant_total=Decimal('-40.00'))


class TestContraintesPaiement:
    def test_montant_nul_refuse(self):
        reservation = ReservationModelFactory(membre=MembreFactory())
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Paiement.objects.create(reservation=reservation, _valeur=Decimal('0.00'), _devise='TND')

    def test_montant_negatif_refuse(self):
        reservation = ReservationModelFactory(membre=MembreFactory())
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Paiement.objects.create(reservation=reservation, _valeur=Decimal('-5.00'), _devise='TND')

    def test_un_seul_paiement_par_reservation(self):
        """OneToOne : la contrainte UNIQUE en base interdit un 2e paiement,
        même si la garde applicative (`InitierPaiementUseCase`) était contournée."""
        reservation = ReservationModelFactory(membre=MembreFactory())
        Paiement.objects.create(reservation=reservation, _valeur=Decimal('40.00'), _devise='TND')
        with pytest.raises(IntegrityError):
            with transaction.atomic():
                Paiement.objects.create(reservation=reservation, _valeur=Decimal('40.00'), _devise='TND')
