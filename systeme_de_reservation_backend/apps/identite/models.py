"""Contexte support Identité — modèles Django directs (pas de DDD tactique
complet imposé pour ce contexte, cf. brief). `Utilisateur` est l'AUTH_USER_MODEL,
`Membre`/`Gestionnaire` sont les deux profils (généralisation UML du CH2)."""

from __future__ import annotations

import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models


class UtilisateurManager(BaseUserManager):
    """Manager custom : pas de champ `username`, connexion par `email`."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError("L'email est obligatoire.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Un superuser doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Un superuser doit avoir is_superuser=True.')
        return self._create_user(email, password, **extra_fields)


class Utilisateur(AbstractUser):
    """AUTH_USER_MODEL. Connexion par email (pas de `username`)."""

    username = None
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20, blank=True, default='')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UtilisateurManager()

    def __str__(self) -> str:
        return self.email


class Membre(models.Model):
    """Profil membre (rôle : parcourir/réserver/payer). Généralisation UML de Utilisateur."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='membre')
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Membre({self.utilisateur.email})'


class Gestionnaire(models.Model):
    """Profil gestionnaire (rôle : administrer les salles, consulter les KPIs)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    utilisateur = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gestionnaire'
    )
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Gestionnaire({self.utilisateur.email})'
