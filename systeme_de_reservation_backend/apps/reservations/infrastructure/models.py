"""Modèles ORM Django du contexte Réservation.

Ces modèles sont des objets de persistance distincts des Entities du
domaine (`domain/entities.py`) : ils n'héritent d'aucune classe du domaine
et ne portent aucune logique métier. La traduction entre les deux mondes
est faite exclusivement par `infrastructure/mappers.py`.

Base unique partagée par tous les contextes (`public`), FKs inter-contextes
autorisées : `Reservation.membre` référence `identite.Membre` directement.
`Reservation` n'a PAS de FK vers `Paiement` : c'est `paiements.Paiement`
qui porte un `OneToOneField(Reservation, related_name='paiement')`, évitant
une dépendance circulaire entre les deux apps.
"""

from __future__ import annotations

import uuid

from django.db import models


class EspaceCoworking(models.Model):
    """Table `espace_coworking` — persistance de l'Entity `Salle` du domaine."""

    class TypeEspace(models.TextChoices):
        BUREAU_PRIVE = 'BUREAU_PRIVE', 'Bureau privé'
        OPEN_SPACE = 'OPEN_SPACE', 'Open space'
        SALLE_REUNION = 'SALLE_REUNION', 'Salle de réunion'

    id_espace = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=100, unique=True)
    type_espace = models.CharField(max_length=20, choices=TypeEspace.choices)
    capacite = models.IntegerField()
    tarif_horaire = models.DecimalField(max_digits=8, decimal_places=2)
    disponible = models.BooleanField(default=True)
    localisation = models.CharField(max_length=150, null=True, blank=True)
    id_gestionnaire = models.UUIDField()  # référence au Gestionnaire créateur (pas de FK : profil facultatif)
    equipements = models.TextField(blank=True, default='')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'espace_coworking'
        constraints = [
            models.CheckConstraint(condition=models.Q(capacite__gt=0), name='espace_coworking_capacite_positive'),
            models.CheckConstraint(
                condition=models.Q(tarif_horaire__gte=0), name='espace_coworking_tarif_horaire_non_negatif'
            ),
            models.CheckConstraint(
                condition=models.Q(type_espace__in=['BUREAU_PRIVE', 'OPEN_SPACE', 'SALLE_REUNION']),
                name='espace_coworking_type_espace_valide',
            ),
        ]

    def __str__(self) -> str:
        return f'{self.nom} ({self.id_espace})'


class CreneauSlot(models.Model):
    """Ressource CRUD `creneaux` : une plage horaire proposée à la réservation
    pour une salle donnée. Distincte du Value Object `Creneau` du domaine
    (date/heure_debut/heure_fin + `chevauche()`), utilisé en interne par
    l'agrégat `Reservation` pour ses invariants — `CreneauSlot` est le
    catalogue applicatif sur lequel s'appuie `POST /reservations/ {creneau, membre}`.
    """

    class Statut(models.TextChoices):
        DISPONIBLE = 'DISPONIBLE', 'Disponible'
        RESERVE = 'RESERVE', 'Réservé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    espace = models.ForeignKey(EspaceCoworking, on_delete=models.CASCADE, related_name='creneaux')
    date = models.DateField()
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.DISPONIBLE)

    class Meta:
        db_table = 'creneau'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(heure_fin__gt=models.F('heure_debut')), name='creneau_heure_fin_apres_debut'
            ),
            models.UniqueConstraint(
                fields=['espace', 'date', 'heure_debut', 'heure_fin'], name='creneau_unique_par_salle'
            ),
        ]

    def __str__(self) -> str:
        return f'{self.espace_id} {self.date} {self.heure_debut}-{self.heure_fin} ({self.statut})'


class Reservation(models.Model):
    """Table `reservation` — persistance de l'Aggregate Root `Reservation` du domaine."""

    class Statut(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        CONFIRMEE = 'CONFIRMEE', 'Confirmée'
        ANNULEE = 'ANNULEE', 'Annulée'

    id_reservation = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creneau_slot = models.ForeignKey(
        CreneauSlot, on_delete=models.RESTRICT, null=True, blank=True, related_name='reservations'
    )
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.EN_ATTENTE)
    montant_total = models.DecimalField(max_digits=10, decimal_places=2)
    espace = models.ForeignKey(
        EspaceCoworking,
        on_delete=models.RESTRICT,
        db_column='id_espace',
        related_name='reservations',
    )
    membre = models.ForeignKey(
        'identite.Membre',
        on_delete=models.RESTRICT,
        db_column='id_membre',
        related_name='reservations',
    )

    class Meta:
        db_table = 'reservation'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(date_fin__gt=models.F('date_debut')), name='reservation_date_fin_apres_date_debut'
            ),
            models.CheckConstraint(
                condition=models.Q(montant_total__gte=0), name='reservation_montant_total_non_negatif'
            ),
            models.CheckConstraint(
                condition=models.Q(statut__in=['EN_ATTENTE', 'CONFIRMEE', 'ANNULEE']),
                name='reservation_statut_valide',
            ),
            # Anti-chevauchement (EXCLUDE USING gist, scope CONFIRMEE
            # uniquement) : pas exprimable via l'ORM, cf. migration 0002.
        ]

    def __str__(self) -> str:
        return f'Reservation {self.id_reservation} ({self.statut})'
