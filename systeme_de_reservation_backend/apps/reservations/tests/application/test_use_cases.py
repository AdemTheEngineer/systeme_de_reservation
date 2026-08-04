"""Tests de la couche application avec repositories fake en mémoire (pas de DB)."""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from apps.reservations.application.dto import (
    AnnulerReservationInput,
    ConfirmerReservationInput,
    CreerReservationInput,
    LibererCreneauInput,
)
from apps.reservations.application.exceptions import (
    CreneauIndisponibleError,
    CreneauIntrouvableError,
    ReservationIntrouvableError,
)
from apps.reservations.application.use_cases.annuler_reservation import AnnulerReservationUseCase
from apps.reservations.application.use_cases.confirmer_reservation import ConfirmerReservationUseCase
from apps.reservations.application.use_cases.consulter_disponibilites import (
    ListerReservationsUseCase,
    ListerSallesDisponiblesUseCase,
)
from apps.reservations.application.use_cases.liberer_creneau import LibererCreneauUseCase
from apps.reservations.application.use_cases.reserver_creneau import ReserverCreneauUseCase
from apps.reservations.domain.enums import StatutReservation, StatutSalle
from apps.reservations.domain.events import ReservationAnnulee, ReservationConfirmee, ReservationCreee
from apps.reservations.domain.exceptions import ChevauchementCreneauError
from apps.reservations.domain.entities import Salle
from apps.reservations.domain.value_objects import Montant
from apps.reservations.tests.application.fakes import (
    FakeCreneauSlotRepository,
    FakeDisponibiliteRepository,
    FakeEventPublisher,
    FakeReservationReadRepository,
    FakeReservationRepository,
    FakeSalleRepository,
)


def make_salle(statut: StatutSalle = StatutSalle.ACTIVE, tarif: str = '20') -> Salle:
    return Salle(
        id=uuid.uuid4(),
        nom='Salle Ibn Khaldoun',
        capacite=10,
        equipements='Vidéoprojecteur',
        tarif_horaire=Montant(Decimal(tarif), 'TND'),
        statut=statut,
    )


class Contexte:
    """Regroupe les fakes nécessaires à un scénario bout-en-bout."""

    def __init__(self, salles: list[Salle]):
        self.salle_repository = FakeSalleRepository(salles)
        self.reservation_repository = FakeReservationRepository()
        self.creneau_slot_repository = FakeCreneauSlotRepository()
        self.event_publisher = FakeEventPublisher()

    def reserver_use_case(self) -> ReserverCreneauUseCase:
        return ReserverCreneauUseCase(
            self.salle_repository, self.reservation_repository, self.creneau_slot_repository, self.event_publisher
        )

    def confirmer_use_case(self) -> ConfirmerReservationUseCase:
        return ConfirmerReservationUseCase(self.reservation_repository, self.event_publisher)

    def annuler_use_case(self) -> AnnulerReservationUseCase:
        return AnnulerReservationUseCase(
            self.reservation_repository, self.creneau_slot_repository, self.event_publisher
        )

    def liberer_use_case(self) -> LibererCreneauUseCase:
        return LibererCreneauUseCase(
            self.reservation_repository, self.creneau_slot_repository, self.event_publisher
        )

    def ajouter_creneau(self, salle: Salle, jour=date(2026, 7, 20), debut=time(9, 0), fin=time(11, 0)) -> uuid.UUID:
        return self.creneau_slot_repository.ajouter(salle.id, jour, debut, fin)


class TestReserverCreneauUseCase:
    def test_reservation_reussie(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle)

        output = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))

        assert output.reservation.statut == StatutReservation.EN_ATTENTE.value
        assert output.reservation.acompte == Decimal('40.00')  # 2h * 20
        assert ctx.reservation_repository.get_by_id(output.reservation.id) is not None
        assert ctx.creneau_slot_repository.obtenir(creneau_id)['statut'] == 'RESERVE'
        assert len(ctx.event_publisher.events_publies) == 1
        assert isinstance(ctx.event_publisher.events_publies[0], ReservationCreee)

    def test_acompte_duree_fractionnaire_arrondi_correctement(self):
        """EF-10 : 1h30 × 19.99 TND = 29.985 → 29.99 (ROUND_HALF_UP, 2 décimales)."""
        salle = make_salle(tarif='19.99')
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle, debut=time(9, 0), fin=time(10, 30))

        output = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))

        assert output.reservation.acompte == Decimal('29.99')
        assert output.reservation.devise == 'TND'

    def test_creneau_introuvable_leve_exception(self):
        ctx = Contexte([make_salle()])
        with pytest.raises(CreneauIntrouvableError):
            ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=uuid.uuid4(), membre_id=uuid.uuid4()))

    def test_creneau_deja_reserve_leve_exception(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.creneau_slot_repository.ajouter(
            salle.id, date(2026, 7, 20), time(9, 0), time(11, 0), statut='RESERVE'
        )
        with pytest.raises(CreneauIndisponibleError):
            ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))

    def test_deuxieme_en_attente_sur_meme_salle_ne_bloque_pas(self):
        """Règle CH2 v2 : EN_ATTENTE ne bloque pas — seul le creneau_slot lui-même
        empêche une double réservation du même slot exact."""
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_1 = ctx.ajouter_creneau(salle, debut=time(9, 0), fin=time(11, 0))
        creneau_2 = ctx.ajouter_creneau(salle, debut=time(10, 0), fin=time(12, 0))

        ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_1, membre_id=uuid.uuid4()))
        output_2 = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_2, membre_id=uuid.uuid4()))

        assert output_2.reservation.statut == StatutReservation.EN_ATTENTE.value

    def test_chevauchement_contre_confirmee_leve_exception(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_1 = ctx.ajouter_creneau(salle, debut=time(9, 0), fin=time(11, 0))
        creneau_2 = ctx.ajouter_creneau(salle, debut=time(10, 0), fin=time(12, 0))

        premiere = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_1, membre_id=uuid.uuid4()))
        ctx.confirmer_use_case().execute(
            ConfirmerReservationInput(reservation_id=premiere.reservation.id, paiement_id=uuid.uuid4())
        )

        with pytest.raises(ChevauchementCreneauError):
            ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_2, membre_id=uuid.uuid4()))


class TestConfirmerReservationUseCase:
    def test_confirmer_reussi(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle)
        creation = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))
        ctx.event_publisher.events_publies.clear()

        paiement_id = uuid.uuid4()
        output = ctx.confirmer_use_case().execute(
            ConfirmerReservationInput(reservation_id=creation.reservation.id, paiement_id=paiement_id)
        )

        assert output.reservation.statut == StatutReservation.CONFIRMEE.value
        assert output.reservation.paiement_id == paiement_id
        assert len(ctx.event_publisher.events_publies) == 1
        assert isinstance(ctx.event_publisher.events_publies[0], ReservationConfirmee)

    def test_reservation_introuvable_leve_exception(self):
        ctx = Contexte([make_salle()])
        with pytest.raises(ReservationIntrouvableError):
            ctx.confirmer_use_case().execute(
                ConfirmerReservationInput(reservation_id=uuid.uuid4(), paiement_id=uuid.uuid4())
            )

    def test_confirmation_concurrente_chevauchante_leve_exception(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_1 = ctx.ajouter_creneau(salle, debut=time(9, 0), fin=time(11, 0))
        creneau_2 = ctx.ajouter_creneau(salle, debut=time(10, 0), fin=time(12, 0))

        premiere = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_1, membre_id=uuid.uuid4()))
        seconde = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_2, membre_id=uuid.uuid4()))

        ctx.confirmer_use_case().execute(
            ConfirmerReservationInput(reservation_id=premiere.reservation.id, paiement_id=uuid.uuid4())
        )
        with pytest.raises(ChevauchementCreneauError):
            ctx.confirmer_use_case().execute(
                ConfirmerReservationInput(reservation_id=seconde.reservation.id, paiement_id=uuid.uuid4())
            )


class TestAnnulerReservationUseCase:
    def test_annuler_reussi_et_libere_le_creneau(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle)
        creation = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))
        ctx.confirmer_use_case().execute(
            ConfirmerReservationInput(reservation_id=creation.reservation.id, paiement_id=uuid.uuid4())
        )
        ctx.event_publisher.events_publies.clear()

        output = ctx.annuler_use_case().execute(AnnulerReservationInput(reservation_id=creation.reservation.id))

        assert output.reservation.statut == StatutReservation.ANNULEE.value
        assert ctx.creneau_slot_repository.obtenir(creneau_id)['statut'] == 'DISPONIBLE'
        assert len(ctx.event_publisher.events_publies) == 1
        assert isinstance(ctx.event_publisher.events_publies[0], ReservationAnnulee)

    def test_annuler_reservation_en_attente_leve_exception(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle)
        creation = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))

        with pytest.raises(Exception):
            ctx.annuler_use_case().execute(AnnulerReservationInput(reservation_id=creation.reservation.id))

    def test_reservation_introuvable_leve_exception(self):
        ctx = Contexte([make_salle()])
        with pytest.raises(ReservationIntrouvableError):
            ctx.annuler_use_case().execute(AnnulerReservationInput(reservation_id=uuid.uuid4()))


class TestLibererCreneauUseCase:
    def test_liberer_reussi_et_libere_le_creneau(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle)
        creation = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))
        ctx.event_publisher.events_publies.clear()

        output = ctx.liberer_use_case().execute(LibererCreneauInput(reservation_id=creation.reservation.id))

        assert output.reservation.statut == StatutReservation.ANNULEE.value
        assert ctx.creneau_slot_repository.obtenir(creneau_id)['statut'] == 'DISPONIBLE'
        assert len(ctx.event_publisher.events_publies) == 1
        assert isinstance(ctx.event_publisher.events_publies[0], ReservationAnnulee)


class TestListerReservationsUseCase:
    def test_filtre_par_membre(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_1 = ctx.ajouter_creneau(salle, jour=date(2026, 7, 20))
        creneau_2 = ctx.ajouter_creneau(salle, jour=date(2026, 7, 21))

        membre_a, membre_b = uuid.uuid4(), uuid.uuid4()
        ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_1, membre_id=membre_a))
        ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_2, membre_id=membre_b))

        resultats = ListerReservationsUseCase(
            FakeReservationReadRepository(ctx.reservation_repository)
        ).execute(membre_id=membre_a)

        assert len(resultats) == 1
        assert resultats[0].membre_id == membre_a


class TestListerSallesDisponiblesUseCase:
    def test_exclut_salle_avec_conflit_confirme(self):
        salle_libre = make_salle()
        salle_occupee = make_salle()
        ctx = Contexte([salle_libre, salle_occupee])
        creneau_id = ctx.ajouter_creneau(salle_occupee, debut=time(9, 0), fin=time(11, 0))
        creation = ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))
        ctx.confirmer_use_case().execute(
            ConfirmerReservationInput(reservation_id=creation.reservation.id, paiement_id=uuid.uuid4())
        )

        use_case = ListerSallesDisponiblesUseCase(
            FakeDisponibiliteRepository(ctx.salle_repository, ctx.reservation_repository)
        )
        resultats = use_case.execute(date(2026, 7, 20), time(10, 0), time(12, 0))

        ids = {r.id for r in resultats}
        assert salle_libre.id in ids
        assert salle_occupee.id not in ids

    def test_inclut_salle_avec_conflit_seulement_en_attente(self):
        salle = make_salle()
        ctx = Contexte([salle])
        creneau_id = ctx.ajouter_creneau(salle, debut=time(9, 0), fin=time(11, 0))
        ctx.reserver_use_case().execute(CreerReservationInput(creneau_id=creneau_id, membre_id=uuid.uuid4()))

        use_case = ListerSallesDisponiblesUseCase(
            FakeDisponibiliteRepository(ctx.salle_repository, ctx.reservation_repository)
        )
        resultats = use_case.execute(date(2026, 7, 20), time(10, 0), time(12, 0))

        assert salle.id in {r.id for r in resultats}

    def test_exclut_salle_inactive(self):
        salle_inactive = make_salle(StatutSalle.INACTIVE)
        ctx = Contexte([salle_inactive])

        use_case = ListerSallesDisponiblesUseCase(
            FakeDisponibiliteRepository(ctx.salle_repository, ctx.reservation_repository)
        )
        resultats = use_case.execute(date(2026, 7, 20), time(9, 0), time(11, 0))

        assert resultats == []
