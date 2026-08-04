"""Contexte support Paiement — modèle Django direct (app légère, pas de DDD
tactique complet imposé). Mock/simulé : pas de vraie passerelle de paiement.

`reservation = OneToOneField(reservations.Reservation, related_name='paiement')`
porte la relation dans CE sens (Paiement -> Reservation) pour éviter une
dépendance circulaire entre apps (cf. `apps/reservations/infrastructure/mappers.py`).
"""

from __future__ import annotations

import uuid

from django.db import models


class Paiement(models.Model):
    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        ACCEPTE = 'ACCEPTE', 'Accepté'
        REFUSE = 'REFUSE', 'Refusé'

    class Moyen(models.TextChoices):
        CARTE = 'CARTE', 'Carte bancaire'
        VIREMENT = 'VIREMENT', 'Virement'
        ESPECES = 'ESPECES', 'Espèces'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reservation = models.OneToOneField(
        'reservations.Reservation', on_delete=models.RESTRICT, related_name='paiement'
    )
    _valeur = models.DecimalField(max_digits=8, decimal_places=2, db_column='montant_valeur')
    _devise = models.CharField(max_length=3, default='TND', db_column='montant_devise')
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.EN_ATTENTE)
    moyen = models.CharField(max_length=10, choices=Moyen.choices, default=Moyen.CARTE)
    reference_externe = models.CharField(max_length=100, null=True, blank=True)
    date_paiement = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'paiement'
        constraints = [
            models.CheckConstraint(condition=models.Q(_valeur__gt=0), name='paiement_montant_strictement_positif'),
        ]

    def __str__(self) -> str:
        return f'Paiement {self.id} ({self.statut})'
