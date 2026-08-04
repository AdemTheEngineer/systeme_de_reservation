"""DTOs de la couche application — frontière entre `interfaces` et `domain`.

Ces objets ne portent aucune logique métier ; ils transportent des
données déjà validées vers/depuis les use cases. Python pur (pas de
dépendance Django), pour rester utilisables aussi bien par les tests
`application` (repository fake, sans DB) que par `interfaces/api/`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal

from apps.reservations.domain.entities import Reservation


@dataclass(frozen=True)
class CreerReservationInput:
    creneau_id: uuid.UUID
    membre_id: uuid.UUID


@dataclass(frozen=True)
class ReservationDTO:
    id: uuid.UUID
    salle_id: uuid.UUID
    membre_id: uuid.UUID
    date: date
    heure_debut: time
    heure_fin: time
    statut: str
    acompte: Decimal
    devise: str
    paiement_id: uuid.UUID | None
    date_creation: datetime
    date_modification: datetime

    @staticmethod
    def from_entity(reservation: Reservation) -> 'ReservationDTO':
        return ReservationDTO(
            id=reservation.id,
            salle_id=reservation.salle_id,
            membre_id=reservation.membre_id,
            date=reservation.creneau.date,
            heure_debut=reservation.creneau.heure_debut,
            heure_fin=reservation.creneau.heure_fin,
            statut=reservation.statut.value,
            acompte=reservation.acompte.valeur,
            devise=reservation.acompte.devise,
            paiement_id=reservation.paiement_id,
            date_creation=reservation.date_creation,
            date_modification=reservation.date_modification,
        )

    @staticmethod
    def from_row(row: dict) -> 'ReservationDTO':
        """Construit le DTO directement depuis une ligne aplatie (CQRS, EF-07) —
        sans reconstruire l'Aggregate Root ni ses Value Objects."""
        return ReservationDTO(**row)


@dataclass(frozen=True)
class CreerReservationOutput:
    reservation: ReservationDTO


@dataclass(frozen=True)
class ConfirmerReservationInput:
    reservation_id: uuid.UUID
    paiement_id: uuid.UUID


@dataclass(frozen=True)
class ConfirmerReservationOutput:
    reservation: ReservationDTO


@dataclass(frozen=True)
class AnnulerReservationInput:
    reservation_id: uuid.UUID


@dataclass(frozen=True)
class AnnulerReservationOutput:
    reservation: ReservationDTO


@dataclass(frozen=True)
class LibererCreneauInput:
    reservation_id: uuid.UUID


@dataclass(frozen=True)
class LibererCreneauOutput:
    reservation: ReservationDTO


@dataclass(frozen=True)
class DisponibiliteQuery:
    salle_id: uuid.UUID
    date: date


@dataclass(frozen=True)
class SalleDisponibleDTO:
    id: uuid.UUID
    nom: str
    capacite: int
    tarif_horaire: Decimal
    devise: str


@dataclass(frozen=True)
class TauxOccupationDTO:
    salle_id: uuid.UUID
    nom: str
    heures_reservees: Decimal
    heures_disponibles: Decimal
    taux: Decimal


@dataclass(frozen=True)
class RevenuPeriodeDTO:
    nombre_reservations: int
    somme_acomptes: Decimal
    devise: str


@dataclass(frozen=True)
class DashboardKPIDTO:
    periode_debut: date
    periode_fin: date
    occupation: list[TauxOccupationDTO]
    revenu: RevenuPeriodeDTO
