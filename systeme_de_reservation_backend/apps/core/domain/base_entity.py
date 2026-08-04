"""Shared Kernel — classe de base pour les Entities et Aggregate Roots.

Pur Python : aucune dépendance à Django. Une Entity se distingue d'un Value
Object par son identité (`id`) : deux Entities sont égales si et seulement
si leurs `id` sont égaux, indépendamment de leurs autres attributs.
"""

from __future__ import annotations

import uuid


class Entity:
    """Classe de base pour toute Entity ou Aggregate Root du domaine."""

    id: uuid.UUID

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        if type(self) is not type(other):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))
