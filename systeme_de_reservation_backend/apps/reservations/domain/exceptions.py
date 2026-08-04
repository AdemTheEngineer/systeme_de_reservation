"""Exceptions du domaine Réservation — Python pur, aucune dépendance Django.

Ces exceptions portent des violations d'invariants métier. Elles sont
attrapées et mappées vers des codes HTTP au niveau de `interfaces/api/`,
jamais interprétées dans le domaine lui-même.
"""

from __future__ import annotations


class DomainException(Exception):
    """Classe de base pour toute exception du domaine Réservation."""


class CreneauInvalideError(DomainException):
    """Le créneau est invalide (heure_debut >= heure_fin)."""


class ChevauchementCreneauError(DomainException):
    """Le créneau demandé chevauche une réservation EN_ATTENTE ou CONFIRMEE existante sur la même salle."""


class SalleInactiveError(DomainException):
    """La salle n'est pas ACTIVE : elle ne peut pas être réservée."""


class MontantInvalideError(DomainException):
    """Le montant (acompte, tarif horaire...) ne respecte pas les règles de validité (positivité, décimales)."""


class TransitionInvalideError(DomainException):
    """La transition d'état demandée n'est pas autorisée depuis le statut courant de la réservation."""
