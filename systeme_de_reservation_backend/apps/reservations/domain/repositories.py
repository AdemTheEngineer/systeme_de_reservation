"""Interfaces abstraites des Repositories du domaine Réservation.

Python pur, aucune dépendance Django. Les implémentations concrètes (Django
ORM) vivent dans `infrastructure/repositories.py` et dépendent de ces
interfaces — jamais l'inverse.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import date as date_type
from datetime import time as time_type

from apps.reservations.domain.entities import Reservation, Salle


class ReservationRepository(ABC):
    @abstractmethod
    def get_by_id(self, reservation_id: uuid.UUID) -> Reservation | None:
        """Récupère une réservation par son id, ou None si elle n'existe pas."""

    @abstractmethod
    def save(self, reservation: Reservation, creneau_slot_id: uuid.UUID | None = None) -> None:
        """Persiste une réservation (création ou mise à jour).

        `creneau_slot_id` ne s'applique qu'à la création : lie la ligne
        `reservation` au `CreneauSlot` (ressource `creneaux`) dont elle est
        issue — ce lien n'est pas un concept du domaine, seulement de
        l'infrastructure (cf. `infrastructure/models.py::CreneauSlot`).
        """

    @abstractmethod
    def obtenir_creneau_slot_id(self, reservation_id: uuid.UUID) -> uuid.UUID | None:
        """Id du `CreneauSlot` lié à cette réservation, si présent (pour la libérer à l'annulation)."""

    @abstractmethod
    def lister_par_salle_et_date(self, salle_id: uuid.UUID, date: date_type) -> list[Reservation]:
        """Liste les réservations existantes sur une salle pour une date donnée
        (utilisé pour la vérification anti-chevauchement, EF-09)."""


class SalleRepository(ABC):
    @abstractmethod
    def get_by_id(self, salle_id: uuid.UUID) -> Salle | None:
        """Récupère une salle par son id, ou None si elle n'existe pas."""


class CreneauSlotRepository(ABC):
    """Port CRUD pour la ressource `creneaux` (catalogue de plages réservables).

    N'est pas un Repository d'Aggregate Root : `CreneauSlot` est un simple
    catalogue applicatif, sans invariant tactique propre — d'où le retour
    en `dict` plutôt qu'en Entity (même logique que les ports de lecture
    CQRS ci-dessous).
    """

    @abstractmethod
    def obtenir(self, creneau_id: uuid.UUID) -> dict | None:
        """Retourne {id, salle_id, date, heure_debut, heure_fin, statut} ou None."""

    @abstractmethod
    def marquer_reserve(self, creneau_id: uuid.UUID) -> None:
        """Passe le statut à RESERVE (à la création d'une réservation, quel que soit son statut)."""

    @abstractmethod
    def marquer_disponible(self, creneau_id: uuid.UUID) -> None:
        """Repasse le statut à DISPONIBLE (annulation ou échec de paiement — cancel-and-release)."""


class ReservationReadRepository(ABC):
    """Port de lecture CQRS : ne reconstruit jamais l'Aggregate Root.

    Utilisé par les Query use cases (`consulter_disponibilites`, EF-07) —
    retourne des lignes déjà aplaties (`dict`), pas des Entities, pour
    éviter le coût et la sémantique d'un chargement d'agrégat sur une
    simple lecture.
    """

    @abstractmethod
    def lister(
        self,
        membre_id: uuid.UUID | None = None,
        salle_id: uuid.UUID | None = None,
    ) -> list[dict]:
        """Liste des réservations (filtrage optionnel), triées par date de création décroissante."""


class DisponibiliteRepository(ABC):
    """Port de lecture CQRS pour la disponibilité des salles (EF-07)."""

    @abstractmethod
    def lister_salles_disponibles(
        self,
        date: date_type,
        heure_debut: time_type,
        heure_fin: time_type,
    ) -> list[dict]:
        """Salles ACTIVES sans réservation CONFIRMEE chevauchant le créneau donné."""


class KPIRepository(ABC):
    """Port de lecture pour les indicateurs gestionnaire (EF-16→18)."""

    @abstractmethod
    def taux_occupation_par_salle(self, debut: date_type, fin: date_type) -> list[dict]:
        """Par salle ACTIVE : {salle_id, nom, heures_reservees, heures_disponibles, taux}
        sur `[debut, fin]` — heures_reservees = somme des durées des réservations
        CONFIRMEE chevauchant la période ; heures_disponibles = nb_jours * 24h
        (aucune notion d'heures d'ouverture dans le domaine)."""

    @abstractmethod
    def revenu_periode(self, debut: date_type, fin: date_type) -> dict:
        """{nombre_reservations, somme_acomptes, devise} pour les réservations
        CONFIRMEE dont le paiement (ACCEPTE) est daté dans `[debut, fin]`."""
