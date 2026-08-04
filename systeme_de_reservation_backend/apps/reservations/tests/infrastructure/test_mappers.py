"""Fidélité des mappers Entity ↔ modèle ORM : aller-retour sans perte.

Complète `test_repositories.py` (qui passe par les repositories) en testant
les mappers directement, champ par champ.
"""

import uuid
from datetime import date, time
from decimal import Decimal

import pytest

from apps.identite.tests.factories import MembreFactory
from apps.paiements.models import Paiement
from apps.reservations.domain.entities import Reservation as ReservationEntity
from apps.reservations.domain.enums import StatutReservation, StatutSalle
from apps.reservations.domain.value_objects import Creneau, Montant
from apps.reservations.infrastructure.mappers import ReservationMapper, SalleMapper
from apps.reservations.infrastructure.models import Reservation as ReservationModel
from apps.reservations.tests.factories import EspaceCoworkingFactory, ReservationModelFactory

pytestmark = pytest.mark.django_db


class TestSalleMapper:
    def test_to_domain_champ_par_champ(self):
        espace = EspaceCoworkingFactory(
            nom='Salle Dougga', capacite=12, tarif_horaire=Decimal('35.50'), equipements='Écran, visio'
        )
        salle = SalleMapper.to_domain(espace)
        assert salle.id == espace.id_espace
        assert salle.nom == 'Salle Dougga'
        assert salle.capacite == 12
        assert salle.tarif_horaire == Montant(Decimal('35.50'), 'TND')
        assert salle.equipements == 'Écran, visio'
        assert salle.statut == StatutSalle.ACTIVE

    def test_disponible_false_devient_inactive(self):
        salle = SalleMapper.to_domain(EspaceCoworkingFactory(disponible=False))
        assert salle.statut == StatutSalle.INACTIVE


class TestReservationMapperRoundTrip:
    def test_entity_vers_modele_vers_entity_sans_perte(self):
        espace = EspaceCoworkingFactory()
        membre = MembreFactory()
        entity = ReservationEntity.creer(
            salle=SalleMapper.to_domain(espace),
            membre_id=membre.id,
            creneau=Creneau(date(2026, 8, 1), time(9, 30), time(11, 45)),
            acompte=Montant(Decimal('45.00'), 'TND'),
        )

        model = ReservationMapper.to_model(entity)
        model.save()
        recharge = ReservationMapper.to_domain(ReservationModel.objects.get(pk=entity.id))

        assert recharge.id == entity.id
        assert recharge.creneau == entity.creneau
        assert recharge.statut == entity.statut
        assert recharge.acompte == entity.acompte
        assert recharge.membre_id == entity.membre_id
        assert recharge.salle_id == entity.salle_id
        assert recharge.paiement_id is None

    def test_to_model_met_a_jour_l_instance_existante(self):
        membre = MembreFactory()
        model = ReservationModelFactory(membre=membre)
        entity = ReservationMapper.to_domain(model)
        entity.confirmer(uuid.uuid4())

        rendu = ReservationMapper.to_model(entity, model)

        assert rendu is model  # mise à jour en place, pas de nouvelle ligne
        assert rendu.statut == StatutReservation.CONFIRMEE.value

    def test_to_domain_lit_le_paiement_via_la_relation_inverse(self):
        model = ReservationModelFactory(membre=MembreFactory())
        paiement = Paiement.objects.create(reservation=model, _valeur=Decimal('40.00'), _devise='TND')

        entity = ReservationMapper.to_domain(ReservationModel.objects.get(pk=model.pk))

        assert entity.paiement_id == paiement.id
