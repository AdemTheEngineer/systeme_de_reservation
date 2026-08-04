"""Factories `factory_boy` pour les tests DB-backed (infrastructure/API)."""

from __future__ import annotations

from decimal import Decimal

import factory

from apps.paiements.models import Paiement


class PaiementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Paiement
        # factory_boy ignore les attributs de classe préfixés `_` (réservés à
        # son usage interne) : sans ce `rename`, `montant_valeur` partirait à
        # NULL en base. On déclare donc `valeur`/`devise` et on les renomme
        # vers les champs `_valeur`/`_devise` du modèle.
        rename = {'valeur': '_valeur', 'devise': '_devise'}

    # `reservation` n'a pas de défaut : toujours fourni explicitement (OneToOne).
    valeur = Decimal('40.00')
    devise = 'TND'
    statut = Paiement.Statut.ACCEPTE
    moyen = Paiement.Moyen.CARTE
