"""Domain Events du contexte Paiement — Python pur, aucune dépendance Django.

Consommés par `apps.reservations` via le dispatcher in-process
(`apps.core.domain.dispatcher`), câblé dans `apps/core/apps.py::ready()`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass

from apps.core.domain.domain_event import DomainEvent


@dataclass(frozen=True)
class PaiementValide(DomainEvent):
    paiement_id: uuid.UUID
    reservation_id: uuid.UUID


@dataclass(frozen=True)
class PaiementEchoue(DomainEvent):
    paiement_id: uuid.UUID
    reservation_id: uuid.UUID
    raison: str
