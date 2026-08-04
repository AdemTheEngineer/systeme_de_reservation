"""Use case : réserver un créneau (Command).

1. Charge le `CreneauSlot` (ressource `creneaux`), vérifie qu'il est DISPONIBLE.
2. Charge la salle liée, vérifie qu'elle est ACTIVE (EF-14).
3. Calcule l'acompte à partir de la durée et du tarif horaire (EF-10).
4. Charge les réservations déjà CONFIRMEE sur la salle/date, délègue la
   validation des invariants à `Reservation.creer(...)` (EF-09).
5. Persiste, lie la réservation au `CreneauSlot`, le passe à RESERVE.
6. Publie `ReservationCreee` (EF-15) — le paiement est initié séparément
   par le client via `POST /paiements/`, pas automatiquement ici.
"""

from __future__ import annotations

from apps.reservations.application.dto import CreerReservationInput, CreerReservationOutput, ReservationDTO
from apps.reservations.application.exceptions import (
    CreneauIndisponibleError,
    CreneauIntrouvableError,
    SalleIntrouvableError,
)
from apps.reservations.domain.entities import Reservation
from apps.reservations.domain.event_publisher import EventPublisher
from apps.reservations.domain.repositories import CreneauSlotRepository, ReservationRepository, SalleRepository
from apps.reservations.domain.value_objects import Creneau, Montant


class ReserverCreneauUseCase:
    def __init__(
        self,
        salle_repository: SalleRepository,
        reservation_repository: ReservationRepository,
        creneau_slot_repository: CreneauSlotRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._salle_repository = salle_repository
        self._reservation_repository = reservation_repository
        self._creneau_slot_repository = creneau_slot_repository
        self._event_publisher = event_publisher

    def execute(self, input_dto: CreerReservationInput) -> CreerReservationOutput:
        creneau_slot = self._creneau_slot_repository.obtenir(input_dto.creneau_id)
        if creneau_slot is None:
            raise CreneauIntrouvableError(f"Aucun créneau avec l'id {input_dto.creneau_id}.")
        if creneau_slot['statut'] != 'DISPONIBLE':
            raise CreneauIndisponibleError(f"Le créneau {input_dto.creneau_id} n'est pas disponible.")

        salle = self._salle_repository.get_by_id(creneau_slot['salle_id'])
        if salle is None:
            raise SalleIntrouvableError(f"Aucune salle avec l'id {creneau_slot['salle_id']}.")

        creneau = Creneau(
            date=creneau_slot['date'],
            heure_debut=creneau_slot['heure_debut'],
            heure_fin=creneau_slot['heure_fin'],
        )
        acompte = Montant(creneau.duree_heures * salle.tarif_horaire.valeur, salle.tarif_horaire.devise)

        reservations_confirmees = self._reservation_repository.lister_par_salle_et_date(salle.id, creneau.date)

        reservation = Reservation.creer(
            salle=salle,
            membre_id=input_dto.membre_id,
            creneau=creneau,
            acompte=acompte,
            reservations_existantes=reservations_confirmees,
        )

        # Cf. note de timing de publication dans confirmer_reservation.py.
        self._reservation_repository.save(reservation, creneau_slot_id=creneau_slot['id'])
        self._creneau_slot_repository.marquer_reserve(creneau_slot['id'])
        self._event_publisher.publish_all(reservation.pull_domain_events())

        return CreerReservationOutput(reservation=ReservationDTO.from_entity(reservation))
