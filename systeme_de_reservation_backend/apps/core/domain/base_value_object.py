"""Shared Kernel — mixin pour les Value Objects.

Les Value Objects du projet sont implémentés avec `@dataclass(frozen=True)`,
ce qui fournit déjà `__eq__`/`__hash__` par valeur et l'immutabilité. Ce
mixin documente l'intention et sert de point d'extension commun (ex. si un
Value Object a besoin de comportement partagé au-delà de l'égalité).
"""

from __future__ import annotations


class ValueObject:
    """Marqueur pour les Value Objects immuables, égaux par valeur.

    À utiliser en combinaison avec `@dataclass(frozen=True)` :

        @dataclass(frozen=True)
        class Montant(ValueObject):
            valeur: Decimal
            devise: str
    """

    __slots__ = ()
