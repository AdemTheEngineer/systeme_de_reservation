"""Implémentations concrètes (Django ORM) des Repositories abstraits du domaine."""

from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from datetime import timezone as dt_timezone
from decimal import Decimal

from django.db import IntegrityError
from django.db.models import Exists, OuterRef
from django.utils import timezone as django_timezone

from apps.reservations.domain.entities import Reservation as ReservationEntity
from apps.reservations.domain.entities import Salle as SalleEntity
from apps.reservations.domain.exceptions import ChevauchementCreneauError
from apps.reservations.domain.repositories import (
    CreneauSlotRepository,
    DisponibiliteRepository,
    KPIRepository,
    ReservationReadRepository,
    ReservationRepository,
    SalleRepository,
)
from apps.reservations.infrastructure.mappers import ReservationMapper, SalleMapper
from apps.reservations.infrastructure.models import CreneauSlot as CreneauSlotModel
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel


class DjangoSalleRepository(SalleRepository):
    def get_by_id(self, salle_id: uuid.UUID) -> SalleEntity | None:
        try:
            model = EspaceCoworkingModel.objects.get(pk=salle_id)
        except EspaceCoworkingModel.DoesNotExist:
            return None
        return SalleMapper.to_domain(model)


class DjangoCreneauSlotRepository(CreneauSlotRepository):
    def obtenir(self, creneau_id: uuid.UUID) -> dict | None:
        try:
            model = CreneauSlotModel.objects.get(pk=creneau_id)
        except CreneauSlotModel.DoesNotExist:
            return None
        return {
            'id': model.id,
            'salle_id': model.espace_id,
            'date': model.date,
            'heure_debut': model.heure_debut,
            'heure_fin': model.heure_fin,
            'statut': model.statut,
        }

    def marquer_reserve(self, creneau_id: uuid.UUID) -> None:
        CreneauSlotModel.objects.filter(pk=creneau_id).update(statut=CreneauSlotModel.Statut.RESERVE)

    def marquer_disponible(self, creneau_id: uuid.UUID) -> None:
        CreneauSlotModel.objects.filter(pk=creneau_id).update(statut=CreneauSlotModel.Statut.DISPONIBLE)


class DjangoReservationRepository(ReservationRepository):
    def get_by_id(self, reservation_id: uuid.UUID) -> ReservationEntity | None:
        try:
            model = ReservationModel.objects.select_related('espace').get(pk=reservation_id)
        except ReservationModel.DoesNotExist:
            return None
        return ReservationMapper.to_domain(model)

    def save(self, reservation: ReservationEntity, creneau_slot_id: uuid.UUID | None = None) -> None:
        try:
            model = ReservationModel.objects.get(pk=reservation.id)
        except ReservationModel.DoesNotExist:
            model = None
        model = ReservationMapper.to_model(reservation, model)
        if creneau_slot_id is not None:
            model.creneau_slot_id = creneau_slot_id
        try:
            model.save()
        except IntegrityError as exc:
            # Course entre deux confirmations concurrentes : la contrainte
            # GIST EXCLUDE (`ex_reservation_no_overlap`) a rejeté l'écriture.
            raise ChevauchementCreneauError(
                f"Conflit de créneau détecté en base pour la réservation {reservation.id}."
            ) from exc

    def obtenir_creneau_slot_id(self, reservation_id: uuid.UUID) -> uuid.UUID | None:
        return ReservationModel.objects.filter(pk=reservation_id).values_list('creneau_slot_id', flat=True).first()

    def lister_par_salle_et_date(self, salle_id: uuid.UUID, date: date_type) -> list[ReservationEntity]:
        debut_jour = datetime.combine(date, time_type.min, tzinfo=dt_timezone.utc)
        fin_jour = datetime.combine(date, time_type.max, tzinfo=dt_timezone.utc)
        queryset = ReservationModel.objects.filter(
            espace_id=salle_id,
            date_debut__lt=fin_jour,
            date_fin__gt=debut_jour,
        )
        return [ReservationMapper.to_domain(model) for model in queryset]


class DjangoReservationReadRepository(ReservationReadRepository):
    """Port de lecture CQRS : `.values()` renvoie des dicts, sans jamais
    instancier de modèle ORM ni reconstruire l'Aggregate Root (EF-07)."""

    _CHAMPS = (
        'id_reservation',
        'espace_id',
        'membre_id',
        'date_debut',
        'date_fin',
        'statut',
        'montant_total',
        'paiement__id',
        'date_creation',
        'date_modification',
    )

    def lister(self, membre_id: uuid.UUID | None = None, salle_id: uuid.UUID | None = None) -> list[dict]:
        queryset = ReservationModel.objects.order_by('-date_creation')
        if membre_id is not None:
            queryset = queryset.filter(membre_id=membre_id)
        if salle_id is not None:
            queryset = queryset.filter(espace_id=salle_id)

        return [_vers_ligne_reservation(row) for row in queryset.values(*self._CHAMPS)]


class DjangoDisponibiliteRepository(DisponibiliteRepository):
    def lister_salles_disponibles(
        self,
        date: date_type,
        heure_debut: time_type,
        heure_fin: time_type,
    ) -> list[dict]:
        debut = datetime.combine(date, heure_debut, tzinfo=dt_timezone.utc)
        fin = datetime.combine(date, heure_fin, tzinfo=dt_timezone.utc)

        chevauchement = ReservationModel.objects.filter(
            espace=OuterRef('pk'),
            statut=ReservationModel.Statut.CONFIRMEE,
            date_debut__lt=fin,
            date_fin__gt=debut,
        )
        queryset = (
            EspaceCoworkingModel.objects.filter(disponible=True)
            .annotate(a_conflit=Exists(chevauchement))
            .filter(a_conflit=False)
            .values('id_espace', 'nom', 'capacite', 'tarif_horaire')
        )
        return [
            {
                'id': row['id_espace'],
                'nom': row['nom'],
                'capacite': row['capacite'],
                'tarif_horaire': row['tarif_horaire'],
                'devise': 'TND',  # devise unique du système, non portée par le modèle (cf. mappers.py)
            }
            for row in queryset
        ]


class DjangoKPIRepository(KPIRepository):
    def taux_occupation_par_salle(self, debut: date_type, fin: date_type) -> list[dict]:
        debut_dt = datetime.combine(debut, time_type.min, tzinfo=dt_timezone.utc)
        fin_dt = datetime.combine(fin, time_type.max, tzinfo=dt_timezone.utc)
        nb_jours = (fin - debut).days + 1
        heures_disponibles = Decimal(nb_jours * 24)

        resultats = []
        for espace in EspaceCoworkingModel.objects.filter(disponible=True):
            reservations = ReservationModel.objects.filter(
                espace=espace,
                statut=ReservationModel.Statut.CONFIRMEE,
                date_debut__lt=fin_dt,
                date_fin__gt=debut_dt,
            ).values_list('date_debut', 'date_fin')

            heures_reservees = Decimal('0')
            for r_debut, r_fin in reservations:
                chevauchement_debut = max(r_debut, debut_dt)
                chevauchement_fin = min(r_fin, fin_dt)
                duree = chevauchement_fin - chevauchement_debut
                heures_reservees += Decimal(duree.total_seconds()) / Decimal(3600)

            taux = (heures_reservees / heures_disponibles) if heures_disponibles else Decimal('0')
            resultats.append(
                {
                    'salle_id': espace.id_espace,
                    'nom': espace.nom,
                    'heures_reservees': heures_reservees.quantize(Decimal('0.01')),
                    'heures_disponibles': heures_disponibles,
                    'taux': taux.quantize(Decimal('0.0001')),
                }
            )
        return resultats

    def revenu_periode(self, debut: date_type, fin: date_type) -> dict:
        """Ancré sur `date_paiement` (quand l'argent a été encaissé), pas sur la
        date d'usage de la salle : `nombre_reservations` = nombre de paiements
        ACCEPTE sur la période (chacun correspond à une réservation, OneToOne)."""
        from apps.paiements.models import Paiement

        debut_dt = datetime.combine(debut, time_type.min, tzinfo=dt_timezone.utc)
        fin_dt = datetime.combine(fin, time_type.max, tzinfo=dt_timezone.utc)

        montants = Paiement.objects.filter(
            statut=Paiement.Statut.ACCEPTE,
            date_paiement__gte=debut_dt,
            date_paiement__lte=fin_dt,
        ).values_list('_valeur', flat=True)
        montants = list(montants)

        return {
            'nombre_reservations': len(montants),
            'somme_acomptes': sum(montants, Decimal('0.00')),
            'devise': 'TND',
        }


def _vers_ligne_reservation(row: dict) -> dict:
    debut = django_timezone.localtime(row['date_debut'], dt_timezone.utc)
    fin = django_timezone.localtime(row['date_fin'], dt_timezone.utc)
    return {
        'id': row['id_reservation'],
        'salle_id': row['espace_id'],
        'membre_id': row['membre_id'],
        'date': debut.date(),
        'heure_debut': debut.time(),
        'heure_fin': fin.time(),
        'statut': row['statut'],
        'acompte': row['montant_total'],
        'devise': 'TND',  # devise unique du système, non portée par le modèle (cf. mappers.py)
        'paiement_id': row['paiement__id'],
        'date_creation': row['date_creation'],
        'date_modification': row['date_modification'],
    }
