class PaiementImpossibleError(Exception):
    """La réservation n'est pas dans un état permettant d'initier un paiement
    (déjà payée, annulée, montant incorrect, ou paiement déjà existant)."""


class ReservationIntrouvableError(Exception):
    """Aucune réservation ne correspond à l'id fourni pour ce paiement."""
