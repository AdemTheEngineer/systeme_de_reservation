"""Factories `factory_boy` pour les tests DB-backed (infrastructure/API).

Django uniquement — cf. note dans `apps/identite/tests/factories.py`.
"""

from __future__ import annotations

from datetime import date, time
from decimal import Decimal

import factory

from apps.reservations.infrastructure.models import CreneauSlot, EspaceCoworking
from apps.reservations.infrastructure.models import Reservation as ReservationModel


class EspaceCoworkingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EspaceCoworking

    nom = factory.Sequence(lambda n: f'Salle {n}')
    type_espace = EspaceCoworking.TypeEspace.SALLE_REUNION
    capacite = 8
    tarif_horaire = Decimal('20.00')
    disponible = True
    id_gestionnaire = factory.Faker('uuid4')
    equipements = ''


class CreneauSlotFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CreneauSlot

    espace = factory.SubFactory(EspaceCoworkingFactory)
    date = date(2026, 8, 1)
    heure_debut = time(9, 0)
    heure_fin = time(11, 0)
    statut = CreneauSlot.Statut.DISPONIBLE


class ReservationModelFactory(factory.django.DjangoModelFactory):
    """Construit directement la ligne ORM (contourne l'agrégat) — utile pour
    poser un état de base en infra/API sans repasser par l'API HTTP."""

    class Meta:
        model = ReservationModel

    creneau_slot = factory.SubFactory(CreneauSlotFactory)
    date_debut = factory.LazyAttribute(lambda o: _combine(o.creneau_slot.date, o.creneau_slot.heure_debut))
    date_fin = factory.LazyAttribute(lambda o: _combine(o.creneau_slot.date, o.creneau_slot.heure_fin))
    statut = ReservationModel.Statut.EN_ATTENTE
    montant_total = Decimal('40.00')
    espace = factory.LazyAttribute(lambda o: o.creneau_slot.espace)

    # `membre` n'a pas de défaut : toujours fourni explicitement par l'appelant
    # (évite une dépendance circulaire de import-time avec `identite.tests.factories`).


def _combine(date_, time_):
    from datetime import datetime, timezone

    return datetime.combine(date_, time_, tzinfo=timezone.utc)
