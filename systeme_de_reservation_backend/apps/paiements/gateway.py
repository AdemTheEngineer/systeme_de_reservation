"""Simulation du prestataire de paiement (mock — pas de passerelle réelle).

Injectable pour les tests (cf. brief : "MockPaymentGateway.traiter(paiement)
-> bool, toujours True par défaut, injectable pour que les tests simulent
un échec sans dépendre d'un vrai hasard").
"""

from __future__ import annotations

from decimal import Decimal


class MockPaymentGateway:
    def traiter(self, montant: Decimal, devise: str, moyen: str) -> bool:
        return True
