"""Value Objects du domaine Réservation — Python pur, aucune dépendance Django.

Immuables (`frozen=True`), égaux par valeur, sans identité propre.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, time
from decimal import ROUND_HALF_UP, Decimal

from apps.core.domain.base_value_object import ValueObject
from apps.reservations.domain.exceptions import CreneauInvalideError, MontantInvalideError

_DEVISE_RE = re.compile(r'^[A-Z]{3}$')


@dataclass(frozen=True)
class Creneau(ValueObject):
    """Un créneau horaire : une date et une plage [heure_debut, heure_fin)."""

    date: date
    heure_debut: time
    heure_fin: time

    def __post_init__(self) -> None:
        if self.heure_debut >= self.heure_fin:
            raise CreneauInvalideError(
                f"heure_debut ({self.heure_debut}) doit être strictement "
                f"antérieure à heure_fin ({self.heure_fin})."
            )

    def chevauche(self, autre: 'Creneau') -> bool:
        """True si ce créneau et `autre` se recouvrent (même date, plages horaires qui s'intersectent)."""
        if self.date != autre.date:
            return False
        return self.heure_debut < autre.heure_fin and autre.heure_debut < self.heure_fin

    @property
    def duree_heures(self) -> Decimal:
        debut = Decimal(self.heure_debut.hour) + Decimal(self.heure_debut.minute) / 60
        fin = Decimal(self.heure_fin.hour) + Decimal(self.heure_fin.minute) / 60
        return fin - debut


@dataclass(frozen=True)
class Montant(ValueObject):
    """Une somme d'argent : une valeur décimale (2 décimales) et une devise ISO 4217."""

    valeur: Decimal
    devise: str = 'TND'

    def __post_init__(self) -> None:
        valeur = self.valeur if isinstance(self.valeur, Decimal) else Decimal(str(self.valeur))
        valeur = valeur.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        object.__setattr__(self, 'valeur', valeur)

        if self.valeur < 0:
            raise MontantInvalideError(f"Le montant ({self.valeur}) ne peut pas être négatif.")
        if not _DEVISE_RE.match(self.devise):
            raise MontantInvalideError(f"Devise invalide (attendu ISO 4217, ex. 'TND') : {self.devise!r}")

    def est_strictement_positif(self) -> bool:
        return self.valeur > 0

    def _meme_devise(self, autre: 'Montant') -> None:
        if self.devise != autre.devise:
            raise MontantInvalideError(
                f"Impossible de comparer des montants de devises différentes : {self.devise} vs {autre.devise}"
            )

    def __add__(self, autre: 'Montant') -> 'Montant':
        self._meme_devise(autre)
        return Montant(self.valeur + autre.valeur, self.devise)

    def __lt__(self, autre: 'Montant') -> bool:
        self._meme_devise(autre)
        return self.valeur < autre.valeur

    def __le__(self, autre: 'Montant') -> bool:
        self._meme_devise(autre)
        return self.valeur <= autre.valeur
