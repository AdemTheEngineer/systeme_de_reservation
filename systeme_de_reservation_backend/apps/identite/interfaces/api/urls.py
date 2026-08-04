from django.urls import path
from rest_framework.routers import DefaultRouter

from apps.identite.interfaces.api.views import (
    GestionnaireViewSet,
    LoginView,
    LogoutView,
    MeView,
    MembreViewSet,
    RefreshView,
)

router = DefaultRouter()
router.register('membres', MembreViewSet, basename='membre')
router.register('gestionnaires', GestionnaireViewSet, basename='gestionnaire')

urlpatterns = [
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/me/', MeView.as_view(), name='auth-me'),
] + router.urls
