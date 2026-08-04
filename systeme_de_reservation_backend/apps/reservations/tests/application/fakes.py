"""Fakes en mémoire pour tester la couche application sans base de données."""

from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import time as time_type

from apps.core.domain.domain_event import DomainEvent
from apps.reservations.domain.entities import Reservation, Salle
from apps.reservations.domain.enums import StatutReservation
from apps.reservations.domain.event_publisher import EventPublisher
from apps.reservations.domain.repositories import (
    CreneauSlotRepository,
    DisponibiliteRepository,
    ReservationReadRepository,
    ReservationRepository,
    SalleRepository,
)


class FakeSalleRepository(SalleRepository):
    def __init__(self, salles: list[Salle] | None = None) -> None:
        self._salles = {salle.id: salle for salle in (salles or [])}

    def get_by_id(self, salle_id: uuid.UUID) -> Salle | None:
        return self._salles.get(salle_id)

    def ajouter(self, salle: Salle) -> None:
        self._salles[salle.id] = salle


class FakeCreneauSlotRepository(CreneauSlotRepository):
    def __init__(self) -> None:
        self._creneaux: dict[uuid.UUID, dict] = {}

    def ajouter(self, salle_id: uuid.UUID, date, heure_debut, heure_fin, statut: str = 'DISPONIBLE') -> uuid.UUID:
        creneau_id = uuid.uuid4()
        self._creneaux[creneau_id] = {
            'id': creneau_id,
            'salle_id': salle_id,
            'date': date,
            'heure_debut': heure_debut,
            'heure_fin': heure_fin,
            'statut': statut,
        }
        return creneau_id

    def obtenir(self, creneau_id: uuid.UUID) -> dict | None:
        return self._creneaux.get(creneau_id)

    def marquer_reserve(self, creneau_id: uuid.UUID) -> None:
        if creneau_id in self._creneaux:
            self._creneaux[creneau_id]['statut'] = 'RESERVE'

    def marquer_disponible(self, creneau_id: uuid.UUID) -> None:
        if creneau_id in self._creneaux:
            self._creneaux[creneau_id]['statut'] = 'DISPONIBLE'


class FakeReservationRepository(ReservationRepository):
    def __init__(self) -> None:
        self._reservations: dict[uuid.UUID, Reservation] = {}
        self._creneau_slot_par_reservation: dict[uuid.UUID, uuid.UUID] = {}

    def get_by_id(self, reservation_id: uuid.UUID) -> Reservation | None:
        return self._reservations.get(reservation_id)

    def save(self, reservation: Reservation, creneau_slot_id: uuid.UUID | None = None) -> None:
        self._reservations[reservation.id] = reservation
        if creneau_slot_id is not None:
            self._creneau_slot_par_reservation[reservation.id] = creneau_slot_id

    def obtenir_creneau_slot_id(self, reservation_id: uuid.UUID) -> uuid.UUID | None:
        return self._creneau_slot_par_reservation.get(reservation_id)

    def lister_par_salle_et_date(self, salle_id: uuid.UUID, date: date_type) -> list[Reservation]:
        return [
            r
            for r in self._reservations.values()
            if r.salle_id == salle_id and r.creneau.date == date
        ]


class FakeReservationReadRepository(ReservationReadRepository):
    def __init__(self, reservation_repository: FakeReservationRepository) -> None:
        self._reservation_repository = reservation_repository

    def lister(self, membre_id: uuid.UUID | None = None, salle_id: uuid.UUID | None = None) -> list[dict]:
        resultats = []
        for r in self._reservation_repository._reservations.values():
            if membre_id is not None and r.membre_id != membre_id:
                continue
            if salle_id is not None and r.salle_id != salle_id:
                continue
            resultats.append(
                {
                    'id': r.id,
                    'salle_id': r.salle_id,
                    'membre_id': r.membre_id,
                    'date': r.creneau.date,
                    'heure_debut': r.creneau.heure_debut,
                    'heure_fin': r.creneau.heure_fin,
                    'statut': r.statut.value,
                    'acompte': r.acompte.valeur,
                    'devise': r.acompte.devise,
                    'paiement_id': r.paiement_id,
                    'date_creation': r.date_creation,
                    'date_modification': r.date_modification,
                }
            )
        return resultats


class FakeDisponibiliteRepository(DisponibiliteRepository):
    def __init__(self, salle_repository: FakeSalleRepository, reservation_repository: FakeReservationRepository) -> None:
        self._salle_repository = salle_repository
        self._reservation_repository = reservation_repository

    def lister_salles_disponibles(self, date: date_type, heure_debut: time_type, heure_fin: time_type) -> list[dict]:
        from apps.reservations.domain.value_objects import Creneau

        creneau = Creneau(date=date, heure_debut=heure_debut, heure_fin=heure_fin)
        resultats = []
        for salle in self._salle_repository._salles.values():
            if not salle.est_active():
                continue
            conflit = any(
                r.salle_id == salle.id
                and r.statut == StatutReservation.CONFIRMEE
                and r.creneau.chevauche(creneau)
                for r in self._reservation_repository._reservations.values()
            )
            if not conflit:
                resultats.append(
                    {
                        'id': salle.id,
                        'nom': salle.nom,
                        'capacite': salle.capacite,
                        'tarif_horaire': salle.tarif_horaire.valeur,
                        'devise': salle.tarif_horaire.devise,
                    }
                )
        return resultats


class FakeEventPublisher(EventPublisher):
    def __init__(self) -> None:
        self.events_publies: list[DomainEvent] = []

    def publish(self, event: DomainEvent) -> None:
        self.events_publies.append(event)
