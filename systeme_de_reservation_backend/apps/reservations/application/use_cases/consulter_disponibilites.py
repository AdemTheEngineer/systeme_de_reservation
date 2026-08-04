"""Use cases de lecture (Query — CQRS, EF-07).

Ne passent jamais par l'Aggregate Root : les repositories de lecture
(`ReservationReadRepository`, `DisponibiliteRepository`) retournent des
lignes déjà aplaties, converties directement en DTO — pas d'Entity, pas de
Value Object reconstruits pour une simple lecture.
"""

from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import time as time_type

from apps.reservations.application.dto import ReservationDTO, SalleDisponibleDTO
from apps.reservations.domain.repositories import DisponibiliteRepository, ReservationReadRepository


class ListerReservationsUseCase:
    def __init__(self, reservation_read_repository: ReservationReadRepository) -> None:
        self._reservation_read_repository = reservation_read_repository

    def execute(
        self,
        membre_id: uuid.UUID | None = None,
        salle_id: uuid.UUID | None = None,
    ) -> list[ReservationDTO]:
        rows = self._reservation_read_repository.lister(membre_id=membre_id, salle_id=salle_id)
        return [ReservationDTO.from_row(row) for row in rows]


class ListerSallesDisponiblesUseCase:
    def __init__(self, disponibilite_repository: DisponibiliteRepository) -> None:
        self._disponibilite_repository = disponibilite_repository

    def execute(self, date: date_type, heure_debut: time_type, heure_fin: time_type) -> list[SalleDisponibleDTO]:
        rows = self._disponibilite_repository.lister_salles_disponibles(date, heure_debut, heure_fin)
        return [SalleDisponibleDTO(**row) for row in rows]
