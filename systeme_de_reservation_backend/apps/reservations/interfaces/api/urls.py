from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.reservations.interfaces.api.views import (
    CreneauViewSet,
    DashboardKPIView,
    ReservationViewSet,
    RevenuPeriodeView,
    SalleViewSet,
    SallesDisponiblesView,
    TauxOccupationView,
)

router = DefaultRouter()
router.register('salles', SalleViewSet, basename='salle')
router.register('creneaux', CreneauViewSet, basename='creneau')
router.register('reservations', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('salles/disponibles/', SallesDisponiblesView.as_view(), name='salles-disponibles'),
    path('kpis/occupation/', TauxOccupationView.as_view(), name='kpis-occupation'),
    path('kpis/revenu/', RevenuPeriodeView.as_view(), name='kpis-revenu'),
    path('kpis/dashboard/', DashboardKPIView.as_view(), name='kpis-dashboard'),
] + router.urls
