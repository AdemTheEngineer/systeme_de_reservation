"""Tests d'intégration (PostgreSQL réel, pas SQLite — la contrainte GiST
anti-chevauchement n'existe pas sur SQLite).
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from apps.identite.models import Membre, Utilisateur
from apps.paiements.models import Paiement
from apps.reservations.domain.entities import Reservation as ReservationEntity
from apps.reservations.domain.enums import StatutReservation
from apps.reservations.domain.exceptions import ChevauchementCreneauError
from apps.reservations.domain.value_objects import Creneau, Montant
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel
from apps.reservations.infrastructure.repositories import DjangoReservationRepository, DjangoSalleRepository

pytestmark = pytest.mark.django_db


def make_espace(disponible: bool = True) -> EspaceCoworkingModel:
    return EspaceCoworkingModel.objects.create(
        nom=f'Salle {uuid.uuid4()}',
        type_espace=EspaceCoworkingModel.TypeEspace.SALLE_REUNION,
        capacite=8,
        tarif_horaire=Decimal('20.00'),
        disponible=disponible,
        id_gestionnaire=uuid.uuid4(),
    )


def make_membre() -> Membre:
    utilisateur = Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    return Membre.objects.create(utilisateur=utilisateur)


class TestDjangoSalleRepository:
    def test_get_by_id_existant(self):
        espace = make_espace()
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)
        assert salle is not None
        assert salle.id == espace.id_espace
        assert salle.est_active()

    def test_get_by_id_inexistant(self):
        assert DjangoSalleRepository().get_by_id(uuid.uuid4()) is None

    def test_salle_inactive_mappee_correctement(self):
        espace = make_espace(disponible=False)
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)
        assert not salle.est_active()


class TestDjangoReservationRepository:
    def test_save_puis_get_by_id_round_trip(self):
        espace = make_espace()
        membre = make_membre()
        repo = DjangoReservationRepository()
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)

        reservation = ReservationEntity.creer(
            salle=salle,
            membre_id=membre.id,
            creneau=Creneau(date(2026, 8, 1), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40.00'), 'TND'),
        )
        repo.save(reservation)

        recharge = repo.get_by_id(reservation.id)
        assert recharge is not None
        assert recharge.statut == StatutReservation.EN_ATTENTE
        assert recharge.salle_id == espace.id_espace
        assert recharge.membre_id == membre.id
        assert recharge.creneau == reservation.creneau
        assert recharge.acompte == reservation.acompte
        assert recharge.paiement_id is None

    def test_save_met_a_jour_une_reservation_existante_et_lit_le_paiement_lie(self):
        espace = make_espace()
        membre = make_membre()
        repo = DjangoReservationRepository()
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)

        reservation = ReservationEntity.creer(
            salle=salle,
            membre_id=membre.id,
            creneau=Creneau(date(2026, 8, 1), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40.00'), 'TND'),
        )
        repo.save(reservation)

        paiement = Paiement.objects.create(
            reservation=ReservationModel.objects.get(pk=reservation.id),
            _valeur=Decimal('40.00'),
            _devise='TND',
            statut=Paiement.Statut.ACCEPTE,
        )
        reservation.confirmer(paiement.id)
        repo.save(reservation)

        recharge = repo.get_by_id(reservation.id)
        assert recharge.statut == StatutReservation.CONFIRMEE
        assert recharge.paiement_id == paiement.id
        assert ReservationModel.objects.count() == 1

    def test_lister_par_salle_et_date(self):
        espace = make_espace()
        membre = make_membre()
        repo = DjangoReservationRepository()
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)

        reservation = ReservationEntity.creer(
            salle=salle,
            membre_id=membre.id,
            creneau=Creneau(date(2026, 8, 1), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40.00'), 'TND'),
        )
        repo.save(reservation)

        resultats = repo.lister_par_salle_et_date(espace.id_espace, date(2026, 8, 1))
        assert len(resultats) == 1
        assert resultats[0].id == reservation.id

        assert repo.lister_par_salle_et_date(espace.id_espace, date(2026, 8, 2)) == []

    def test_save_traduit_conflit_gist_en_exception_domaine(self):
        """Deux CONFIRMEE chevauchantes : la contrainte GIST rejette la 2e
        écriture, traduite en `ChevauchementCreneauError` par le repository."""
        espace = make_espace()
        membre = make_membre()
        repo = DjangoReservationRepository()
        salle = DjangoSalleRepository().get_by_id(espace.id_espace)

        r1 = ReservationEntity.creer(
            salle=salle, membre_id=membre.id, creneau=Creneau(date(2026, 8, 1), time(9, 0), time(11, 0)),
            acompte=Montant(Decimal('40.00'), 'TND'),
        )
        repo.save(r1)
        r1.confirmer(uuid.uuid4())
        repo.save(r1)

        r2 = ReservationEntity.creer(
            salle=salle, membre_id=membre.id, creneau=Creneau(date(2026, 8, 1), time(10, 0), time(12, 0)),
            acompte=Montant(Decimal('40.00'), 'TND'),
        )
        repo.save(r2)
        r2.confirmer(uuid.uuid4())
        with pytest.raises(ChevauchementCreneauError):
            with transaction.atomic():
                repo.save(r2)


class TestContrainteExclusionGiST:
    """Défense en profondeur : même en contournant l'agrégat, PostgreSQL doit
    refuser deux réservations CONFIRMEE qui se chevauchent sur la même salle."""

    def test_insertion_directe_de_deux_confirmees_chevauchantes_echoue_en_base(self):
        espace = make_espace()
        membre = make_membre()
        ReservationModel.objects.create(
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            statut=ReservationModel.Statut.CONFIRMEE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                ReservationModel.objects.create(
                    date_debut='2026-08-01T10:00:00+00:00',
                    date_fin='2026-08-01T12:00:00+00:00',
                    statut=ReservationModel.Statut.CONFIRMEE,
                    montant_total=Decimal('40.00'),
                    espace=espace,
                    membre=membre,
                )

    def test_deux_en_attente_chevauchantes_sont_autorisees(self):
        """Règle CH2 v2 : seule CONFIRMEE bloque — deux EN_ATTENTE identiques passent."""
        espace = make_espace()
        membre = make_membre()
        ReservationModel.objects.create(
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            statut=ReservationModel.Statut.EN_ATTENTE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )
        ReservationModel.objects.create(
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            statut=ReservationModel.Statut.EN_ATTENTE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )
        assert ReservationModel.objects.count() == 2

    def test_creneaux_chevauchants_annulee_et_en_attente_sont_autorises(self):
        espace = make_espace()
        membre = make_membre()
        ReservationModel.objects.create(
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            statut=ReservationModel.Statut.ANNULEE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )
        ReservationModel.objects.create(
            date_debut='2026-08-01T09:00:00+00:00',
            date_fin='2026-08-01T11:00:00+00:00',
            statut=ReservationModel.Statut.EN_ATTENTE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )
        assert ReservationModel.objects.count() == 2
