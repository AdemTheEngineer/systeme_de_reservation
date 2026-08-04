"""Permissions DRF — autorisation, pas de règle métier.

Le membre appelant est désormais résolu via JWT (`request.user.membre`,
cf. `apps.identite`), remplaçant le stand-in `X-Membre-Id` d'une itération
précédente sans Identité réelle.
"""

from __future__ import annotations

from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.reservations.domain.entities import Reservation


class EstProprietaireDeLaReservation(BasePermission):
    """Seul le membre propriétaire d'une réservation peut la modifier (EF-13)."""

    message = "Seul le membre propriétaire de la réservation peut effectuer cette action."

    def has_object_permission(self, request, view, obj: Reservation) -> bool:
        membre = getattr(request.user, 'membre', None)
        return membre is not None and membre.id == obj.membre_id


class EstGestionnaireOuLectureSeule(BasePermission):
    """Lecture : tout utilisateur authentifié. Écriture : gestionnaire uniquement (`salles`, `creneaux`)."""

    message = "Réservé aux gestionnaires."

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and hasattr(request.user, 'gestionnaire'))
