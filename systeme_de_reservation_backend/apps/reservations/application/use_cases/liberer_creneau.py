"""Use case : libérer le créneau suite à un paiement échoué, déclenché par
l'événement `PaiementEchoue` émis par `apps.paiements` — câblé via le
dispatcher in-process, pas exposé en HTTP (transition système, pas une
action membre — cf. `Reservation.liberer()` vs `annuler()`)."""

from __future__ import annotations

from apps.reservations.application.dto import LibererCreneauInput, LibererCreneauOutput, ReservationDTO
from apps.reservations.application.exceptions import ReservationIntrouvableError
from apps.reservations.domain.event_publisher import EventPublisher
from apps.reservations.domain.repositories import CreneauSlotRepository, ReservationRepository


class LibererCreneauUseCase:
    def __init__(
        self,
        reservation_repository: ReservationRepository,
        creneau_slot_repository: CreneauSlotRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repository = reservation_repository
        self._creneau_slot_repository = creneau_slot_repository
        self._event_publisher = event_publisher

    def execute(self, input_dto: LibererCreneauInput) -> LibererCreneauOutput:
        reservation = self._reservation_repository.get_by_id(input_dto.reservation_id)
        if reservation is None:
            raise ReservationIntrouvableError(f"Aucune réservation avec l'id {input_dto.reservation_id}.")

        reservation.liberer()

        creneau_slot_id = self._reservation_repository.obtenir_creneau_slot_id(reservation.id)
        self._reservation_repository.save(reservation)
        if creneau_slot_id is not None:
            self._creneau_slot_repository.marquer_disponible(creneau_slot_id)
        self._event_publisher.publish_all(reservation.pull_domain_events())

        return LibererCreneauOutput(reservation=ReservationDTO.from_entity(reservation))
