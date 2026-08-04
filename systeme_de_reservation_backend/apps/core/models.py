"""Table d'audit append-only (Shared Kernel).

Peuplée exclusivement par le trigger PL/pgSQL `audit_log_trigger` (cf.
migration `0002_audit_triggers`), jamais par du code applicatif Django —
d'où l'absence de méthode `save()`/use case dédiés : ce modèle ne sert
qu'à la lecture (admin, futurs endpoints de consultation d'audit).
"""

from __future__ import annotations

from django.contrib.postgres.indexes import BrinIndex
from django.db import models


class AuditLog(models.Model):
    table_name = models.CharField(max_length=100)
    operation = models.CharField(max_length=10)
    row_id = models.CharField(max_length=64)
    # BigIntegerField, pas UUIDField : `Utilisateur` (AUTH_USER_MODEL) garde
    # le PK entier par défaut de `AbstractUser`, c'est cet id que porte le
    # token JWT (`SIMPLE_JWT['USER_ID_FIELD'] = 'id'`).
    acteur_id = models.BigIntegerField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    donnees = models.JSONField()
    horodatage = models.DateTimeField()

    class Meta:
        db_table = 'audit_log'
        indexes = [
            BrinIndex(fields=['horodatage'], name='audit_log_horodatage_brin'),
        ]

    def __str__(self) -> str:
        return f'{self.table_name}#{self.row_id} {self.operation} @ {self.horodatage}'
