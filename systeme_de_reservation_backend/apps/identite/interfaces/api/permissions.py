from rest_framework.permissions import BasePermission


class EstGestionnaire(BasePermission):
    """Autorise uniquement les utilisateurs ayant un profil Gestionnaire."""

    message = "Réservé aux gestionnaires."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'gestionnaire')
        )


class EstMembre(BasePermission):
    """Autorise uniquement les utilisateurs ayant un profil Membre."""

    message = "Réservé aux membres."

    def has_permission(self, request, view) -> bool:
        return bool(
            request.user
            and request.user.is_authenticated
            and hasattr(request.user, 'membre')
        )
