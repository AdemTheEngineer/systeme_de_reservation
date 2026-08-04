"""Exceptions de la couche application.

Distinctes des exceptions du domaine (`domain/exceptions.py`) : celles-ci
signalent l'absence d'une ressource ou une règle propre à l'orchestration
d'un use case, pas une violation d'invariant métier. `interfaces/api/`
mappe l'ensemble (domaine + application) vers des codes HTTP.
"""

from __future__ import annotations


class ApplicationException(Exception):
    """Classe de base pour toute exception de la couche application."""


class SalleIntrouvableError(ApplicationException):
    """Aucune salle ne correspond à l'id fourni."""


class ReservationIntrouvableError(ApplicationException):
    """Aucune réservation ne correspond à l'id fourni."""


class CreneauIntrouvableError(ApplicationException):
    """Aucun créneau (ressource `creneaux`) ne correspond à l'id fourni."""


class CreneauIndisponibleError(ApplicationException):
    """Le créneau demandé n'est pas DISPONIBLE (déjà RESERVE)."""
