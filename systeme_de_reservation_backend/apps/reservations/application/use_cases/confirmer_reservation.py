"""Use case : confirmer une réservation, déclenché par l'événement `PaiementValide`
émis par `apps.paiements` (EF-11) — câblé via le dispatcher in-process
(`apps.core.domain.dispatcher`), pas exposé en HTTP.

Comme une réservation EN_ATTENTE ne bloquait pas la création d'une autre
réservation sur le même créneau (règle CH2 v2), le chevauchement est
revérifié ici, contre les réservations déjà CONFIRMEE — cf. la docstring
de `Reservation.confirmer` dans `domain/entities.py`. La contrainte GIST
EXCLUDE en base est le filet de sécurité ultime en cas de course.
"""

from __future__ import annotations

from apps.reservations.application.dto import ConfirmerReservationInput, ConfirmerReservationOutput, ReservationDTO
from apps.reservations.application.exceptions import ReservationIntrouvableError
from apps.reservations.domain.event_publisher import EventPublisher
from apps.reservations.domain.repositories import ReservationRepository


class ConfirmerReservationUseCase:
    def __init__(self, reservation_repository: ReservationRepository, event_publisher: EventPublisher) -> None:
        self._reservation_repository = reservation_repository
        self._event_publisher = event_publisher

    def execute(self, input_dto: ConfirmerReservationInput) -> ConfirmerReservationOutput:
        reservation = self._reservation_repository.get_by_id(input_dto.reservation_id)
        if reservation is None:
            raise ReservationIntrouvableError(f"Aucune réservation avec l'id {input_dto.reservation_id}.")

        autres_confirmees = self._reservation_repository.lister_par_salle_et_date(
            reservation.salle_id, reservation.creneau.date
        )
        reservation.confirmer(input_dto.paiement_id, autres_reservations_confirmees=autres_confirmees)

        # Les events ne sont publiés qu'une fois `save()` revenu : en mode
        # autocommit (par défaut, aucune transaction explicite ouverte par ce
        # use case), la ligne est déjà committée à ce stade. Si ce use case
        # est un jour enveloppé dans un `transaction.atomic()` explicite au
        # niveau interfaces, la publication devra migrer vers
        # `transaction.on_commit(...)` pour respecter la règle "jamais avant
        # le commit". `save()` traduit une violation de la contrainte GIST
        # (course entre deux confirmations concurrentes) en
        # `ChevauchementCreneauError` — cf. infrastructure/repositories.py.
        self._reservation_repository.save(reservation)
        self._event_publisher.publish_all(reservation.pull_domain_events())

        return ConfirmerReservationOutput(reservation=ReservationDTO.from_entity(reservation))
