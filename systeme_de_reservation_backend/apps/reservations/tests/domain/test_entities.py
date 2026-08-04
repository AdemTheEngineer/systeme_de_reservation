import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from apps.reservations.domain.enums import StatutPaiement, StatutReservation, StatutSalle
from apps.reservations.domain.events import ReservationAnnulee, ReservationConfirmee, ReservationCreee
from apps.reservations.domain.exceptions import MontantInvalideError, SalleInactiveError, TransitionInvalideError
from apps.reservations.domain.entities import Paiement, Reservation, Salle
from apps.reservations.domain.value_objects import Creneau, Montant


def make_salle(statut: StatutSalle = StatutSalle.ACTIVE, tarif: str = '20') -> Salle:
    return Salle(
        id=uuid.uuid4(),
        nom='Salle Ibn Khaldoun',
        capacite=10,
        equipements='Vidéoprojecteur, tableau blanc',
        tarif_horaire=Montant(Decimal(tarif), 'TND'),
        statut=statut,
    )


def make_creneau(debut: time = time(9, 0), fin: time = time(11, 0), jour: date = date(2026, 7, 20)) -> Creneau:
    return Creneau(date=jour, heure_debut=debut, heure_fin=fin)


class TestSalle:
    def test_salle_active_est_reservable(self):
        assert make_salle(StatutSalle.ACTIVE).est_active()

    def test_salle_inactive_n_est_pas_reservable(self):
        assert not make_salle(StatutSalle.INACTIVE).est_active()

    def test_tarif_horaire_non_positif_leve_exception(self):
        with pytest.raises(MontantInvalideError):
            make_salle(tarif='0')


class TestPaiement:
    def test_creation(self):
        p = Paiement(
            id=uuid.uuid4(),
            montant=Montant(Decimal('40'), 'TND'),
            statut=StatutPaiement.ACCEPTE,
            reservation_id=uuid.uuid4(),
        )
        assert p.statut == StatutPaiement.ACCEPTE


class TestReservationCreer:
    def test_creation_reussie_statut_en_attente(self):
        salle = make_salle()
        reservation = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=make_creneau(),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        assert reservation.statut == StatutReservation.EN_ATTENTE
        assert reservation.salle_id == salle.id

    def test_creation_emet_reservation_creee(self):
        salle = make_salle()
        reservation = Reservation.creer(
            salle=salle,
            membre_id=uuid.uuid4(),
            creneau=make_creneau(),
            acompte=Montant(Decimal('40'), 'TND'),
        )
        events = reservation.pull_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ReservationCreee)
        assert events[0].reservation_id == reservation.id

    def test_pull_domain_events_vide_la_liste(self):
        salle = make_salle()
        reservation = Reservation.creer(
            salle=salle, membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.pull_domain_events()
        assert reservation.pull_domain_events() == []

    def test_salle_inactive_leve_exception(self):
        salle = make_salle(StatutSalle.INACTIVE)
        with pytest.raises(SalleInactiveError):
            Reservation.creer(
                salle=salle, membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
            )

    def test_acompte_nul_leve_exception(self):
        salle = make_salle()
        with pytest.raises(MontantInvalideError):
            Reservation.creer(
                salle=salle, membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('0'), 'TND')
            )


class TestReservationConfirmer:
    def test_confirmer_depuis_en_attente(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.pull_domain_events()
        paiement_id = uuid.uuid4()
        reservation.confirmer(paiement_id)
        assert reservation.statut == StatutReservation.CONFIRMEE
        assert reservation.paiement_id == paiement_id

    def test_confirmer_emet_reservation_confirmee(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.pull_domain_events()
        reservation.confirmer(uuid.uuid4())
        events = reservation.pull_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ReservationConfirmee)

    def test_confirmer_reservation_deja_confirmee_leve_exception(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.confirmer(uuid.uuid4())
        with pytest.raises(TransitionInvalideError):
            reservation.confirmer(uuid.uuid4())

    def test_confirmer_reservation_annulee_leve_exception(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.liberer()
        with pytest.raises(TransitionInvalideError):
            reservation.confirmer(uuid.uuid4())

    def test_confirmer_revalide_chevauchement_contre_confirmees(self):
        salle = make_salle()
        deja_confirmee = Reservation.creer(
            salle=salle, membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        deja_confirmee.confirmer(uuid.uuid4())

        candidate = Reservation.creer(
            salle=salle, membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        with pytest.raises(Exception):
            candidate.confirmer(uuid.uuid4(), autres_reservations_confirmees=[deja_confirmee])
        assert candidate.statut == StatutReservation.EN_ATTENTE


class TestReservationAnnuler:
    def test_annuler_depuis_en_attente_leve_exception(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        with pytest.raises(TransitionInvalideError):
            reservation.annuler()

    def test_annuler_depuis_confirmee(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.confirmer(uuid.uuid4())
        reservation.pull_domain_events()
        reservation.annuler()
        assert reservation.statut == StatutReservation.ANNULEE

    def test_annuler_emet_reservation_annulee(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.confirmer(uuid.uuid4())
        reservation.pull_domain_events()
        reservation.annuler()
        events = reservation.pull_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ReservationAnnulee)

    def test_annuler_reservation_deja_annulee_leve_exception(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.confirmer(uuid.uuid4())
        reservation.annuler()
        with pytest.raises(TransitionInvalideError):
            reservation.annuler()


class TestReservationLiberer:
    def test_liberer_depuis_en_attente(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.pull_domain_events()
        reservation.liberer()
        assert reservation.statut == StatutReservation.ANNULEE

    def test_liberer_emet_reservation_annulee(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.pull_domain_events()
        reservation.liberer()
        events = reservation.pull_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ReservationAnnulee)

    def test_liberer_reservation_confirmee_leve_exception(self):
        reservation = Reservation.creer(
            salle=make_salle(), membre_id=uuid.uuid4(), creneau=make_creneau(), acompte=Montant(Decimal('40'), 'TND')
        )
        reservation.confirmer(uuid.uuid4())
        with pytest.raises(TransitionInvalideError):
            reservation.liberer()
