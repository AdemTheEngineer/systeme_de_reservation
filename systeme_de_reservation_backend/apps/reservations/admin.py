"""Point d'entrée conventionnel attendu par l'autodiscovery admin de Django.

L'enregistrement réel vit dans `interfaces/admin.py` (cf. structure de
fichiers imposée) ; ce module se contente de l'importer pour que
`django.contrib.admin.autodiscover()` le trouve.
"""

from apps.reservations.interfaces.admin import EspaceCoworkingAdmin, ReservationAdmin

__all__ = ['EspaceCoworkingAdmin', 'ReservationAdmin']
