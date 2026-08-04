"""Enums du domaine Réservation — Python pur, aucune dépendance Django.

Ces enums sont utilisés par les Entities et Value Objects du domaine.
Leur pendant Django (`TextChoices`) vit dans `infrastructure/models.py` ;
c'est le mapper qui fait la traduction entre les deux mondes.
"""

from __future__ import annotations

from enum import Enum


class StatutReservation(str, Enum):
    EN_ATTENTE = 'EN_ATTENTE'
    CONFIRMEE = 'CONFIRMEE'
    ANNULEE = 'ANNULEE'


class StatutPaiement(str, Enum):
    EN_ATTENTE = 'EN_ATTENTE'
    ACCEPTE = 'ACCEPTE'
    REFUSE = 'REFUSE'


class StatutSalle(str, Enum):
    ACTIVE = 'ACTIVE'
    INACTIVE = 'INACTIVE'
