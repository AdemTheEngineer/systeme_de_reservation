"""Middleware positionnant le contexte d'audit (acteur, IP) lu par le
trigger PL/pgSQL `audit_log_trigger` (cf. migration `core.0002_audit_triggers`)
via `current_setting('app.current_user_id')` / `current_setting('app.client_ip')`.

Résout l'utilisateur via JWT directement (et non `request.user`) car
l'authentification DRF/SimpleJWT n'a pas encore eu lieu à ce stade du
middleware stack Django (elle se produit plus tard, dans `APIView.dispatch`).

Utilise `set_config(..., is_local=false)` (portée session, pas transaction) :
en mode autocommit (par défaut), chaque requête ORM est sa propre mini-
transaction, donc un simple `SET LOCAL` ne survivrait pas d'une requête SQL
à l'autre pendant le traitement de la vue. La valeur est réinitialisée à la
fin de la requête HTTP pour ne pas fuiter vers la requête suivante sur une
connexion DB réutilisée (`CONN_MAX_AGE`).
"""

from __future__ import annotations

from django.db import connection
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError


class AuditContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self._jwt_auth = JWTAuthentication()

    def __call__(self, request):
        acteur_id = self._resoudre_acteur_id(request)
        ip = request.META.get('REMOTE_ADDR') or ''

        self._set_config('app.current_user_id', str(acteur_id) if acteur_id else '')
        self._set_config('app.client_ip', ip)
        try:
            return self.get_response(request)
        finally:
            self._set_config('app.current_user_id', '')
            self._set_config('app.client_ip', '')

    def _resoudre_acteur_id(self, request):
        try:
            resultat = self._jwt_auth.authenticate(request)
        except (TokenError, AuthenticationFailed):
            # Token expiré/forgé/du mauvais type (`InvalidToken` hérite
            # d'`AuthenticationFailed`, pas de `TokenError`) : l'acteur d'audit
            # est inconnu, mais le rejet en 401 reste du ressort de DRF plus
            # loin dans la pile — jamais un 500 ici.
            return None
        if resultat is None:
            return None
        utilisateur, _ = resultat
        return utilisateur.id

    @staticmethod
    def _set_config(name: str, value: str) -> None:
        with connection.cursor() as cursor:
            cursor.execute('SELECT set_config(%s, %s, false)', [name, value])
