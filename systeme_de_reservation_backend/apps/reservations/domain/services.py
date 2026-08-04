"""Domain Service : vérification de disponibilité d'un créneau sur une salle.

Python pur, aucune dépendance Django. `Reservation.verifier_chevauchement`
reste la source de vérité pour l'invariant porté par l'agrégat ; cette
fonction est un point d'entrée pratique pour les lectures (ex. Query CQRS
de disponibilité) qui n'ont pas besoin d'instancier une `Reservation` pour
savoir si un créneau est libre.
"""

from __future__ import annotations

import uuid

from apps.reservations.domain.entities import Reservation
from apps.reservations.domain.enums import StatutReservation
from apps.reservations.domain.value_objects import Creneau


def creneau_est_disponible(
    salle_id: uuid.UUID,
    creneau: Creneau,
    reservations_existantes: list[Reservation],
) -> bool:
    """True si aucune réservation CONFIRMEE sur `salle_id` ne chevauche `creneau`."""
    return not any(
        autre.salle_id == salle_id
        and autre.statut == StatutReservation.CONFIRMEE
        and autre.creneau.chevauche(creneau)
        for autre in reservations_existantes
    )
