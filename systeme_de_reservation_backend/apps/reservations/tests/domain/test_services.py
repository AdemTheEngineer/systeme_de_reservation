"""Tests du Domain Service `creneau_est_disponible` (lecture de disponibilité)."""

import uuid
from datetime import date, time
from decimal import Decimal

from apps.reservations.domain.entities import Reservation, Salle
from apps.reservations.domain.enums import StatutSalle
from apps.reservations.domain.services import creneau_est_disponible
from apps.reservations.domain.value_objects import Creneau, Montant

JOUR = date(2026, 7, 20)


def make_salle() -> Salle:
    return Salle(
        id=uuid.uuid4(),
        nom=f'Salle {uuid.uuid4()}',
        capacite=6,
        equipements='',
        tarif_horaire=Montant(Decimal('20'), 'TND'),
        statut=StatutSalle.ACTIVE,
    )


def make_reservation(salle: Salle, debut: time, fin: time, confirmee: bool = True) -> Reservation:
    reservation = Reservation.creer(
        salle=salle,
        membre_id=uuid.uuid4(),
        creneau=Creneau(JOUR, debut, fin),
        acompte=Montant(Decimal('40'), 'TND'),
    )
    if confirmee:
        reservation.confirmer(uuid.uuid4())
    return reservation


def test_disponible_sans_aucune_reservation():
    assert creneau_est_disponible(uuid.uuid4(), Creneau(JOUR, time(9, 0), time(11, 0)), [])


def test_indisponible_si_confirmee_chevauchante():
    salle = make_salle()
    existante = make_reservation(salle, time(9, 0), time(11, 0))
    assert not creneau_est_disponible(salle.id, Creneau(JOUR, time(10, 0), time(12, 0)), [existante])


def test_disponible_si_seulement_en_attente_chevauchante():
    salle = make_salle()
    en_attente = make_reservation(salle, time(9, 0), time(11, 0), confirmee=False)
    assert creneau_est_disponible(salle.id, Creneau(JOUR, time(10, 0), time(12, 0)), [en_attente])


def test_disponible_si_confirmee_sur_une_autre_salle():
    salle_a, salle_b = make_salle(), make_salle()
    existante = make_reservation(salle_a, time(9, 0), time(11, 0))
    assert creneau_est_disponible(salle_b.id, Creneau(JOUR, time(9, 0), time(11, 0)), [existante])


def test_disponible_si_creneaux_contigus():
    salle = make_salle()
    existante = make_reservation(salle, time(9, 0), time(11, 0))
    assert creneau_est_disponible(salle.id, Creneau(JOUR, time(11, 0), time(13, 0)), [existante])
