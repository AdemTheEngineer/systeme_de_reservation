"""Use case (léger) : initier un paiement pour une réservation EN_ATTENTE.

C'est CET appel (`POST /paiements/`), distinct de la création de la
réservation, qui déclenche le mock de paiement et — via le dispatcher
in-process — confirme ou libère la réservation (cf.
`apps/core/apps.py::ready()` pour le câblage, et la docstring de
`Reservation.confirmer` dans `apps/reservations/domain/entities.py` pour
le pourquoi de cette séparation en deux appels API).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from django.db import transaction

from apps.core.domain.dispatcher import dispatcher
from apps.paiements.domain.events import PaiementEchoue, PaiementValide
from apps.paiements.exceptions import PaiementImpossibleError, ReservationIntrouvableError
from apps.paiements.gateway import MockPaymentGateway
from apps.paiements.models import Paiement
from apps.reservations.infrastructure.models import Reservation as ReservationModel


class InitierPaiementUseCase:
    def __init__(self, gateway: MockPaymentGateway | None = None) -> None:
        self._gateway = gateway or MockPaymentGateway()

    @transaction.atomic
    def execute(self, reservation_id: uuid.UUID, montant: Decimal, devise: str, moyen: str) -> Paiement:
        try:
            reservation = ReservationModel.objects.select_for_update().get(pk=reservation_id)
        except ReservationModel.DoesNotExist as exc:
            raise ReservationIntrouvableError(f"Aucune réservation avec l'id {reservation_id}.") from exc

        if reservation.statut != ReservationModel.Statut.EN_ATTENTE:
            raise PaiementImpossibleError(
                f"La réservation {reservation_id} n'est pas EN_ATTENTE (statut actuel : {reservation.statut})."
            )
        if montant != reservation.montant_total:
            raise PaiementImpossibleError(
                f"Le montant du paiement ({montant}) ne correspond pas à l'acompte dû "
                f"({reservation.montant_total})."
            )
        if Paiement.objects.filter(reservation=reservation).exists():
            raise PaiementImpossibleError(f"La réservation {reservation_id} a déjà un paiement.")

        paiement = Paiement.objects.create(
            reservation=reservation,
            _valeur=montant,
            _devise=devise,
            moyen=moyen,
        )

        accepte = self._gateway.traiter(montant, devise, moyen)
        paiement.statut = Paiement.Statut.ACCEPTE if accepte else Paiement.Statut.REFUSE
        paiement.save(update_fields=['statut'])

        if accepte:
            event = PaiementValide(paiement_id=paiement.id, reservation_id=reservation.id_reservation)
        else:
            event = PaiementEchoue(
                paiement_id=paiement.id, reservation_id=reservation.id_reservation, raison='Paiement refusé (mock).'
            )
        transaction.on_commit(lambda: dispatcher.dispatch(event))

        return paiement
