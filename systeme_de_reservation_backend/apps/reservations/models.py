"""Point d'entrée conventionnel attendu par l'app-loading de Django.

L'implémentation réelle des modèles ORM vit dans `infrastructure/models.py`
(cf. structure de fichiers imposée). Django n'auto-importe que le module
`<app>.models` au démarrage : ce fichier ré-exporte donc les modèles pour
que l'enregistrement dans le registre d'apps fonctionne, sans dupliquer
leur définition.
"""

from apps.reservations.infrastructure.models import EspaceCoworking, Reservation

__all__ = ['EspaceCoworking', 'Reservation']
