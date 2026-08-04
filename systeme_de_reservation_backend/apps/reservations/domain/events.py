"""Domain Events émis par l'Aggregate Root `Reservation`.

Python pur, aucune dépendance Django. Les events sont collectés dans
`Reservation._domain_events` et publiés par la couche application, après
le commit de la transaction (jamais avant).
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from apps.core.domain.domain_event import DomainEvent
from apps.reservations.domain.value_objects import Creneau


@dataclass(frozen=True)
class ReservationCreee(DomainEvent):
    reservation_id: uuid.UUID
    salle_id: uuid.UUID
    creneau: Creneau
    date_creation: datetime


@dataclass(frozen=True)
class ReservationConfirmee(DomainEvent):
    reservation_id: uuid.UUID
    paiement_id: uuid.UUID
    date_confirmation: datetime


@dataclass(frozen=True)
class ReservationAnnulee(DomainEvent):
    reservation_id: uuid.UUID
    date_annulation: datetime
