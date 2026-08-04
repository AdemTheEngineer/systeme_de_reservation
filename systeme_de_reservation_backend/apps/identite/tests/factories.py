"""Factories `factory_boy` pour les tests DB-backed (infrastructure/API).

Django uniquement : les tests `domain`/`application` (Python pur) continuent
d'utiliser leurs propres builders locaux (`make_salle`, etc.), pas ces
factories — elles créent de vraies lignes en base.
"""

from __future__ import annotations

import factory

from apps.identite.models import Gestionnaire, Membre, Utilisateur


class UtilisateurFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Utilisateur
        django_get_or_create = ('email',)

    email = factory.Sequence(lambda n: f'utilisateur{n}@test.local')
    telephone = ''

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        password = kwargs.pop('password', 'motdepasse123')
        manager = model_class.objects
        return manager.create_user(password=password, *args, **kwargs)


class MembreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Membre

    utilisateur = factory.SubFactory(UtilisateurFactory)


class GestionnaireFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Gestionnaire

    utilisateur = factory.SubFactory(UtilisateurFactory)
