from __future__ import annotations

from rest_framework import status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from apps.identite.interfaces.api.permissions import EstGestionnaire
from apps.identite.interfaces.api.serializers import (
    GestionnaireSerializer,
    LoginSerializer,
    MembreSerializer,
    UtilisateurMeSerializer,
)
from apps.identite.models import Gestionnaire, Membre


class MembreViewSet(viewsets.ModelViewSet):
    queryset = Membre.objects.select_related('utilisateur').order_by('-date_creation')
    serializer_class = MembreSerializer
    permission_classes = [IsAuthenticated, EstGestionnaire]
    filterset_fields = []
    search_fields = ['utilisateur__email']
    ordering_fields = ['date_creation']


class GestionnaireViewSet(viewsets.ModelViewSet):
    queryset = Gestionnaire.objects.select_related('utilisateur').order_by('-date_creation')
    serializer_class = GestionnaireSerializer
    permission_classes = [IsAuthenticated, EstGestionnaire]
    search_fields = ['utilisateur__email']
    ordering_fields = ['date_creation']


class LoginView(TokenObtainPairView):
    """`POST /auth/login {email, mot_de_passe}` -> access + refresh (200/401)."""

    serializer_class = LoginSerializer
    permission_classes = [AllowAny]


class RefreshView(TokenRefreshView):
    """`POST /auth/refresh {refresh}` -> nouvel access (+ refresh si rotation) (200/401)."""

    permission_classes = [AllowAny]


class LogoutView(APIView):
    """`POST /auth/logout {refresh}` -> blackliste le refresh token (204/401)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh = request.data.get('refresh')
        if not refresh:
            raise ValidationError({'refresh': 'Ce champ est requis.'})
        try:
            RefreshToken(refresh).blacklist()
        except TokenError as exc:
            raise ValidationError({'refresh': 'Token invalide.'}) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """`GET /auth/me` -> profil de l'utilisateur authentifié (200/401)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UtilisateurMeSerializer(request.user).data)
