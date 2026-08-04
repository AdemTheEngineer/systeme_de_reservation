"""Use cases de reporting (EF-16 → EF-18), gestionnaire-only.

Comme les Query use cases de `consulter_disponibilites.py` : lecture pure,
ne passe pas par l'Aggregate Root.
"""

from __future__ import annotations

from datetime import date as date_type

from apps.reservations.application.dto import DashboardKPIDTO, RevenuPeriodeDTO, TauxOccupationDTO
from apps.reservations.domain.repositories import KPIRepository


class ObtenirTauxOccupationUseCase:
    """EF-16 : taux d'occupation par salle sur une période."""

    def __init__(self, kpi_repository: KPIRepository) -> None:
        self._kpi_repository = kpi_repository

    def execute(self, debut: date_type, fin: date_type) -> list[TauxOccupationDTO]:
        rows = self._kpi_repository.taux_occupation_par_salle(debut, fin)
        return [TauxOccupationDTO(**row) for row in rows]


class ObtenirRevenuPeriodeUseCase:
    """EF-17 : nombre de réservations + somme des acomptes encaissés sur une période."""

    def __init__(self, kpi_repository: KPIRepository) -> None:
        self._kpi_repository = kpi_repository

    def execute(self, debut: date_type, fin: date_type) -> RevenuPeriodeDTO:
        row = self._kpi_repository.revenu_periode(debut, fin)
        return RevenuPeriodeDTO(**row)


class ObtenirDashboardKPIUseCase:
    """EF-18 : dashboard agrégeant occupation + revenu."""

    def __init__(self, kpi_repository: KPIRepository) -> None:
        self._occupation_use_case = ObtenirTauxOccupationUseCase(kpi_repository)
        self._revenu_use_case = ObtenirRevenuPeriodeUseCase(kpi_repository)

    def execute(self, debut: date_type, fin: date_type) -> DashboardKPIDTO:
        return DashboardKPIDTO(
            periode_debut=debut,
            periode_fin=fin,
            occupation=self._occupation_use_case.execute(debut, fin),
            revenu=self._revenu_use_case.execute(debut, fin),
        )
