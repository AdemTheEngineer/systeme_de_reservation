"""Tests d'invariants transversaux de l'agrégat Reservation :
anti double-booking (EF-09), créneau invalide, salle inactive (EF-14).
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from apps.reservations.domain.enums import StatutReservation, StatutSalle
from apps.reservations.domain.exceptions import ChevauchementCreneauError, CreneauInvalideError, SalleInactiveError
from apps.reservations.domain.entities import Reservation, Salle
from apps.reservations.domain.value_objects import Creneau, Montant


def make_salle(statut: StatutSalle = StatutSalle.ACTIVE) -> Salle:
    return Salle(
        id=uuid.uuid4(),
        nom='Salle Test',
        capacite=6,
        equipements='',
        tarif_horaire=Montant(Decimal('20'), 'TND'),
        statut=statut,
    )


class TestAntiDoubleBooking:
    def test_reservation_en_attente_ne_bloque_pas_la_creation(self):
        """Règle CH2 v2 : seule une réservation CONFIRMEE bloque un créneau."""
        salle = make_salle()
        en_attente = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        nouvelle = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(10, 0), time(12, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
            reservations_existantes=[en_attente],
        )
        assert nouvelle.statut == StatutReservation.EN_ATTENTE

    def test_chevauchement_sur_meme_salle_leve_exception(self):
        salle = make_salle()
        existante = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        existante.confirmer(uuid.uuid4())
        with pytest.raises(ChevauchementCreneauError):
            Reservation.creer(
                salle=salle,
                membre_id=uuid.uuid4(),
                creneau=Creneau(date(2026, 7, 20), time(10, 0), time(12, 0)),
                acompte=Montant(Decimal('40'), 'TND'),
                reservations_existantes=[existante],
            )

    def test_pas_de_chevauchement_creneaux_disjoints(self):
        salle = make_salle()
        existante = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        nouvelle = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(11, 0), time(13, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
            reservations_existantes=[existante],
        )
        assert nouvelle.statut == StatutReservation.EN_ATTENTE

    def test_chevauchement_ignore_reservation_annulee(self):
        salle = make_salle()
        annulee = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        annulee.liberer()

        nouvelle = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
            reservations_existantes=[annulee],
        )
        assert nouvelle.statut == StatutReservation.EN_ATTENTE

    def test_chevauchement_ignore_autre_salle(self):
        salle_a = make_salle()
        salle_b = make_salle()
        existante = Reservation.creer(
            salle=salle_a,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        nouvelle = Reservation.creer(
            salle=salle_b,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
            reservations_existantes=[existante],
        )
        assert nouvelle.statut == StatutReservation.EN_ATTENTE

    def test_chevauchement_avec_reservation_confirmee_leve_exception(self):
        salle = make_salle()
        confirmee = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        confirmee.confirmer(uuid.uuid4())
        with pytest.raises(ChevauchementCreneauError):
            Reservation.creer(
                salle=salle,
                membre_id=uuid.uuid4(),
                creneau=Creneau(date(2026, 7, 20), time(10, 0), time(12, 0)),
                acompte=Montant(Decimal('40'), 'TND'),
                reservations_existantes=[confirmee],
            )


class TestCreneauInvalide:
    def test_heure_debut_apres_heure_fin_leve_exception_a_la_creation(self):
        with pytest.raises(CreneauInvalideError):
            Creneau(date(2026, 7, 20), time(12, 0), time(9, 0))


class TestSalleInactive:
    def test_reservation_sur_salle_inactive_leve_exception(self):
        salle = make_salle(StatutSalle.INACTIVE)
        with pytest.raises(SalleInactiveError):
            Reservation.creer(
                salle=salle,
                membre_id=uuid.uuid4(),
                creneau=Creneau(date(2026, 7, 20), time(9, 0), time(11, 0)),
                acompte=Montant(Decimal('40'), 'TND'),
            )
