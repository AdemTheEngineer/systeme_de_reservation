"""Use case : annuler une réservation (Command, EF-13, cancel-and-release).

La vérification que l'appelant est bien le membre propriétaire de la
réservation est une préoccupation d'autorisation, portée par
`interfaces/api/permissions.py` — pas par ce use case ni par le domaine.
Autorisé uniquement depuis CONFIRMEE (cf. `Reservation.annuler`) ; libère
le `CreneauSlot` lié pour qu'il redevienne réservable par un autre membre.
"""

from __future__ import annotations

from apps.reservations.application.dto import AnnulerReservationInput, AnnulerReservationOutput, ReservationDTO
from apps.reservations.application.exceptions import ReservationIntrouvableError
from apps.reservations.domain.event_publisher import EventPublisher
from apps.reservations.domain.repositories import CreneauSlotRepository, ReservationRepository


class AnnulerReservationUseCase:
    def __init__(
        self,
        reservation_repository: ReservationRepository,
        creneau_slot_repository: CreneauSlotRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._reservation_repository = reservation_repository
        self._creneau_slot_repository = creneau_slot_repository
        self._event_publisher = event_publisher

    def execute(self, input_dto: AnnulerReservationInput) -> AnnulerReservationOutput:
        reservation = self._reservation_repository.get_by_id(input_dto.reservation_id)
        if reservation is None:
            raise ReservationIntrouvableError(f"Aucune réservation avec l'id {input_dto.reservation_id}.")

        reservation.annuler()

        creneau_slot_id = self._reservation_repository.obtenir_creneau_slot_id(reservation.id)
        # Cf. reserver_creneau.py pour la note sur le timing de publication.
        self._reservation_repository.save(reservation)
        if creneau_slot_id is not None:
            self._creneau_slot_repository.marquer_disponible(creneau_slot_id)
        self._event_publisher.publish_all(reservation.pull_domain_events())

        return AnnulerReservationOutput(reservation=ReservationDTO.from_entity(reservation))
