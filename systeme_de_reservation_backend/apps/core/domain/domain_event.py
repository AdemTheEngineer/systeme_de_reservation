"""Shared Kernel — classe de base des Domain Events.

Pur Python, aucune dépendance à Django. Chaque Domain Event concret est un
`@dataclass(frozen=True)` qui hérite de `DomainEvent` et ajoute ses propres
champs métier. `occurred_at` est généré automatiquement à l'instanciation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc),
        kw_only=True,
    )
