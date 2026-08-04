"""Entities et Aggregate Root du domaine Réservation.

Python pur, aucune dépendance Django. `Reservation` est l'unique Aggregate
Root de ce contexte : toute mutation (création, confirmation, annulation)
passe par ses méthodes, jamais par une modification directe d'attribut.

Règle du CH2 (v2) : seule une réservation CONFIRMEE bloque un créneau ou
peut être annulée — EN_ATTENTE ne bloque rien. Comme le paiement (donc la
confirmation) arrive dans un second appel API distinct de la création, le
chevauchement doit être revérifié à la confirmation (pas seulement à la
création), sinon deux réservations EN_ATTENTE concurrentes sur le même
créneau pourraient toutes les deux être confirmées. `confirmer()` accepte
donc la liste des autres réservations déjà CONFIRMEE pour cette revérification.
La contrainte GIST EXCLUDE en base (`WHERE statut='CONFIRMEE'`) reste le
filet de sécurité en cas de course entre deux confirmations concurrentes.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from apps.core.domain.base_entity import Entity
from apps.core.domain.domain_event import DomainEvent
from apps.reservations.domain.enums import StatutPaiement, StatutReservation, StatutSalle
from apps.reservations.domain.events import ReservationAnnulee, ReservationConfirmee, ReservationCreee
from apps.reservations.domain.exceptions import (
    ChevauchementCreneauError,
    MontantInvalideError,
    SalleInactiveError,
    TransitionInvalideError,
)
from apps.reservations.domain.value_objects import Creneau, Montant


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Salle(Entity):
    """Entity représentant un espace de coworking réservable."""

    def __init__(
        self,
        id: uuid.UUID,
        nom: str,
        capacite: int,
        equipements: str,
        tarif_horaire: Montant,
        statut: StatutSalle = StatutSalle.ACTIVE,
        date_creation: datetime | None = None,
    ) -> None:
        if not tarif_horaire.est_strictement_positif():
            raise MontantInvalideError(
                f"Le tarif horaire de la salle doit être strictement positif, reçu : {tarif_horaire.valeur}"
            )

        self.id = id
        self.nom = nom
        self.capacite = capacite
        self.equipements = equipements
        self.tarif_horaire = tarif_horaire
        self.statut = statut
        self.date_creation = date_creation or _now()

    def est_active(self) -> bool:
        return self.statut == StatutSalle.ACTIVE


class Paiement(Entity):
    """Entity de référence légère — la logique métier du paiement vit dans le microservice Paiement."""

    def __init__(
        self,
        id: uuid.UUID,
        montant: Montant,
        statut: StatutPaiement,
        reservation_id: uuid.UUID,
        reference_externe: str | None = None,
        date_paiement: datetime | None = None,
    ) -> None:
        self.id = id
        self.montant = montant
        self.statut = statut
        self.reservation_id = reservation_id
        self.reference_externe = reference_externe
        self.date_paiement = date_paiement or _now()


class Reservation(Entity):
    """Aggregate Root du contexte Réservation.

    Toute création, confirmation ou annulation passe par les méthodes de
    cette classe. Les Domain Events émis sont collectés dans
    `_domain_events` et doivent être récupérés via `pull_domain_events()`
    par la couche application, après persistance réussie.
    """

    def __init__(
        self,
        id: uuid.UUID,
        creneau: Creneau,
        statut: StatutReservation,
        acompte: Montant,
        membre_id: uuid.UUID,
        salle_id: uuid.UUID,
        paiement_id: uuid.UUID | None = None,
        date_creation: datetime | None = None,
        date_modification: datetime | None = None,
    ) -> None:
        self.id = id
        self.creneau = creneau
        self.statut = statut
        self.acompte = acompte
        self.membre_id = membre_id
        self.salle_id = salle_id
        self.paiement_id = paiement_id
        self.date_creation = date_creation or _now()
        self.date_modification = date_modification or self.date_creation
        self._domain_events: list[DomainEvent] = []

    # -- Factory -----------------------------------------------------------

    @classmethod
    def creer(
        cls,
        salle: Salle,
        membre_id: uuid.UUID,
        creneau: Creneau,
        acompte: Montant,
        reservations_existantes: list['Reservation'] | None = None,
    ) -> 'Reservation':
        """Crée une nouvelle réservation EN_ATTENTE en validant les invariants métier.

        - la salle doit être ACTIVE (EF-14)
        - l'acompte doit être strictement positif
        - aucune réservation déjà CONFIRMEE sur la salle ne doit chevaucher
          le créneau demandé (EF-09, anti double-booking) — une réservation
          seulement EN_ATTENTE ne bloque pas la création, cf. `confirmer()`
        """
        if not salle.est_active():
            raise SalleInactiveError(f"La salle {salle.id} est INACTIVE : impossible de la réserver.")
        if not acompte.est_strictement_positif():
            raise MontantInvalideError(f"L'acompte doit être strictement positif, reçu : {acompte.valeur}")

        reservation = cls(
            id=uuid.uuid4(),
            creneau=creneau,
            statut=StatutReservation.EN_ATTENTE,
            acompte=acompte,
            membre_id=membre_id,
            salle_id=salle.id,
        )

        if reservations_existantes:
            reservation.verifier_chevauchement(reservations_existantes)

        reservation._domain_events.append(
            ReservationCreee(
                reservation_id=reservation.id,
                salle_id=reservation.salle_id,
                creneau=reservation.creneau,
                date_creation=reservation.date_creation,
            )
        )
        return reservation

    # -- Invariants ----------------------------------------------------------

    def verifier_chevauchement(self, autres_reservations: list['Reservation']) -> None:
        """Lève `ChevauchementCreneauError` si une autre réservation CONFIRMEE sur la même salle chevauche la sienne."""
        for autre in autres_reservations:
            if autre.id == self.id:
                continue
            if autre.salle_id != self.salle_id:
                continue
            if autre.statut != StatutReservation.CONFIRMEE:
                continue
            if self.creneau.chevauche(autre.creneau):
                raise ChevauchementCreneauError(
                    f"Le créneau demandé chevauche la réservation existante {autre.id} sur la salle {self.salle_id}."
                )

    # -- Transitions d'état ---------------------------------------------------

    def confirmer(
        self,
        paiement_id: uuid.UUID,
        autres_reservations_confirmees: list['Reservation'] | None = None,
    ) -> None:
        """Confirme la réservation suite à un paiement validé (EF-11). Seule EN_ATTENTE -> CONFIRMEE est permise.

        Revérifie l'absence de chevauchement contre les réservations déjà
        CONFIRMEE : comme EN_ATTENTE ne bloquait rien à la création, deux
        réservations concurrentes sur le même créneau ont pu être créées ;
        seule la première à être confirmée doit réussir. La contrainte GIST
        EXCLUDE en base reste le filet de sécurité en cas de course réelle.
        """
        if self.statut != StatutReservation.EN_ATTENTE:
            raise TransitionInvalideError(
                f"Impossible de confirmer une réservation au statut {self.statut} (attendu EN_ATTENTE)."
            )

        if autres_reservations_confirmees:
            self.verifier_chevauchement(autres_reservations_confirmees)

        self.statut = StatutReservation.CONFIRMEE
        self.paiement_id = paiement_id
        self.date_modification = _now()

        self._domain_events.append(
            ReservationConfirmee(
                reservation_id=self.id,
                paiement_id=paiement_id,
                date_confirmation=self.date_modification,
            )
        )

    def annuler(self) -> None:
        """Annule la réservation à l'initiative du membre (EF-13). Autorisé uniquement depuis CONFIRMEE."""
        if self.statut != StatutReservation.CONFIRMEE:
            raise TransitionInvalideError(
                f"Impossible d'annuler une réservation au statut {self.statut} (attendu CONFIRMEE)."
            )

        self.statut = StatutReservation.ANNULEE
        self.date_modification = _now()

        self._domain_events.append(
            ReservationAnnulee(
                reservation_id=self.id,
                date_annulation=self.date_modification,
            )
        )

    def liberer(self) -> None:
        """Libère le créneau suite à un paiement échoué (transition système, pas une action membre).

        Autorisé uniquement depuis EN_ATTENTE — une réservation déjà
        CONFIRMEE ne peut être défaite que via `annuler()`.
        """
        if self.statut != StatutReservation.EN_ATTENTE:
            raise TransitionInvalideError(
                f"Impossible de libérer une réservation au statut {self.statut} (attendu EN_ATTENTE)."
            )

        self.statut = StatutReservation.ANNULEE
        self.date_modification = _now()

        self._domain_events.append(
            ReservationAnnulee(
                reservation_id=self.id,
                date_annulation=self.date_modification,
            )
        )

    # -- Domain Events ---------------------------------------------------------

    def pull_domain_events(self) -> list[DomainEvent]:
        """Retourne les événements en attente et vide la liste interne."""
        events, self._domain_events = self._domain_events, []
        return events
