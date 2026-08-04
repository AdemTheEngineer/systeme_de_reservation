"""Seed du contexte Paiement — adossé au seed Réservation (montants en TND).

Ordre d'exécution du projet :
    1. seed_identite
    2. seed_reservations
    3. seed_paiements   (ce fichier)

Cohérence métier : dans le domaine, une Reservation passe à CONFIRMEE *parce
que* son paiement a été accepté (événement `PaiementAccepte`). Le seed respecte
ce lien de causalité au lieu de tirer un statut au hasard :

    Reservation.CONFIRMEE  -> Paiement.ACCEPTE      (systématique)
    Reservation.EN_ATTENTE -> EN_ATTENTE / REFUSE / pas de paiement
    Reservation.ANNULEE    -> pas de paiement / REFUSE / (rare) ACCEPTE

Le montant repris est `Reservation.montant_total` : aucun écart possible entre
les deux contextes.

Usage :
    uv run python manage.py seed_paiements
    uv run python manage.py seed_paiements --nombre 60
    uv run python manage.py seed_paiements --tout-accepte
    uv run python manage.py seed_paiements --flush            # reset du seed
    uv run python manage.py seed_paiements --flush --nombre 0 # suppression seule
"""

from __future__ import annotations

import random
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.paiements.models import Paiement
from apps.reservations.infrastructure.models import Reservation

# --- Paramètres du jeu de données -------------------------------------------

PREFIXE_SEED = 'SEED-'  # marqueur porté par reference_externe : rend --flush sûr
GRAINE_ALEATOIRE = 2026

SANS_PAIEMENT = '__AUCUN__'  # sentinelle : la réservation reste sans paiement

# Distribution des statuts de paiement, conditionnée au statut de la réservation.
POIDS_PAR_STATUT_RESERVATION = {
    # Invariant du domaine : une réservation confirmée a forcément été payée.
    Reservation.Statut.CONFIRMEE: ((Paiement.Statut.ACCEPTE, 100),),
    # Réservation posée, paiement initié mais non abouti (ou pas encore lancé).
    Reservation.Statut.EN_ATTENTE: ((Paiement.Statut.EN_ATTENTE, 70),
                                    (Paiement.Statut.REFUSE, 15),
                                    (SANS_PAIEMENT, 15)),
    # Annulation avant paiement, ou annulation consécutive à un refus.
    # La part ACCEPTE modélise le cas « payé puis annulé » (remboursement à
    # traiter) : le modèle n'ayant pas de statut REMBOURSE, elle reste marginale.
    Reservation.Statut.ANNULEE: ((SANS_PAIEMENT, 55),
                                 (Paiement.Statut.REFUSE, 35),
                                 (Paiement.Statut.ACCEPTE, 10)),
}

# Moyens de paiement conditionnés au statut : un virement met des jours à
# arriver (d'où sa surreprésentation en attente), les espèces se règlent en
# main propre au comptoir et n'échouent jamais.
POIDS_MOYEN_PAR_STATUT = {
    Paiement.Statut.ACCEPTE: ((Paiement.Moyen.CARTE, 62),
                              (Paiement.Moyen.VIREMENT, 18),
                              (Paiement.Moyen.ESPECES, 20)),
    Paiement.Statut.EN_ATTENTE: ((Paiement.Moyen.VIREMENT, 65),
                                 (Paiement.Moyen.CARTE, 35)),
    Paiement.Statut.REFUSE: ((Paiement.Moyen.CARTE, 80),
                             (Paiement.Moyen.VIREMENT, 20)),
}

# Canal de la référence simulée (aucune vraie passerelle : app mock, cf. docstring
# du modèle). CTP = ClicToPay/SMT, le service e-commerce des banques tunisiennes.
CANAL_PAR_MOYEN = {
    Paiement.Moyen.CARTE: 'CTP',
    Paiement.Moyen.VIREMENT: 'VIR',
    Paiement.Moyen.ESPECES: 'CSH',
}


def _tirage(alea: random.Random, table) -> str:
    return alea.choices([v for v, _ in table], weights=[p for _, p in table], k=1)[0]


class Command(BaseCommand):
    help = "Peuple le contexte Paiement à partir des réservations existantes."

    def add_arguments(self, parser):
        parser.add_argument('--nombre', type=int, default=0,
                            help='Plafond de paiements (0 = toutes les réservations éligibles).')
        parser.add_argument('--tout-accepte', action='store_true',
                            help='Force tous les paiements à ACCEPTE (démo « tout vert »).')
        parser.add_argument('--flush', action='store_true',
                            help='Supprime les paiements du seed avant insertion.')
        parser.add_argument('--seed', type=int, default=GRAINE_ALEATOIRE,
                            help='Graine aléatoire (reproductibilité).')

    @transaction.atomic
    def handle(self, *args, **options):
        plafond: int = options['nombre']
        if plafond < 0:
            raise CommandError('--nombre doit être positif ou nul.')

        alea = random.Random(options['seed'])

        if options['flush']:
            supprimes, _ = Paiement.objects.filter(
                reference_externe__startswith=PREFIXE_SEED
            ).delete()
            self.stdout.write(self.style.WARNING(f'{supprimes} paiement(s) supprimé(s).'))

        if plafond == 0 and options['flush'] and not Reservation.objects.exists():
            self.stdout.write(self.style.SUCCESS('Rien à insérer.'))
            return

        # OneToOne : on ne considère que les réservations encore sans paiement.
        # Tri par date_creation pour que le plafond --nombre coupe chronologiquement.
        candidates = list(
            Reservation.objects
            .filter(paiement__isnull=True)
            .select_related('espace')
            .order_by('date_creation')
        )
        if plafond:
            candidates = candidates[:plafond]

        if not candidates:
            raise CommandError(
                'Aucune réservation sans paiement. Lancez d’abord :\n'
                '  uv run python manage.py seed_reservations\n'
                'ou rejouez ce seed avec --flush.'
            )

        maintenant = timezone.now()
        paiements: list[Paiement] = []
        ignorees = {'sans_paiement': 0, 'montant_nul': 0}

        for index, reservation in enumerate(candidates, start=1):
            statut = self._statut_paiement(alea, reservation, options['tout_accepte'])
            if statut is SANS_PAIEMENT:
                ignorees['sans_paiement'] += 1
                continue

            # Reservation autorise montant_total >= 0, Paiement exige _valeur > 0 :
            # une réservation gratuite ne peut donc pas porter de paiement.
            montant = Decimal(reservation.montant_total).quantize(Decimal('0.01'))
            if montant <= 0:
                ignorees['montant_nul'] += 1
                continue

            moyen = _tirage(alea, POIDS_MOYEN_PAR_STATUT[statut])

            paiements.append(
                Paiement(
                    reservation=reservation,
                    _valeur=montant,      # repris tel quel : zéro écart avec la réservation
                    _devise='TND',
                    statut=statut,
                    moyen=moyen,
                    reference_externe=(
                        f'{PREFIXE_SEED}{CANAL_PAR_MOYEN[moyen]}-2026-'
                        f'{index:06d}-{alea.randint(1000, 9999)}'
                    ),
                )
            )

        if not paiements:
            self.stdout.write(self.style.WARNING('Aucun paiement à créer.'))
            return

        crees = Paiement.objects.bulk_create(paiements, batch_size=200)

        # date_paiement est auto_now_add : sans retouche les lignes porteraient
        # toutes le même horodatage. On la replace entre la création de la
        # réservation et le début du créneau (bulk_update ignore auto_now_add).
        for paiement in crees:
            paiement.date_paiement = self._date_paiement(alea, paiement, maintenant)
        Paiement.objects.bulk_update(crees, ['date_paiement'], batch_size=200)

        self._rapport(crees, ignorees, len(candidates))

    # --- Règles -------------------------------------------------------------

    def _statut_paiement(self, alea, reservation: Reservation, tout_accepte: bool) -> str:
        if tout_accepte:
            return Paiement.Statut.ACCEPTE
        table = POIDS_PAR_STATUT_RESERVATION.get(
            reservation.statut, ((Paiement.Statut.EN_ATTENTE, 100),)
        )
        return _tirage(alea, table)

    def _date_paiement(self, alea, paiement: Paiement, maintenant):
        """Le paiement intervient après la réservation et avant le créneau."""
        reservation = paiement.reservation
        debut = reservation.date_creation
        fin = min(reservation.date_debut, maintenant)
        if fin <= debut:
            return debut
        secondes = int((fin - debut).total_seconds())
        # Un paiement en attente vient d'être initié : on le colle au début de
        # la fenêtre plutôt que de l'étaler sur toute sa durée.
        if paiement.statut == Paiement.Statut.EN_ATTENTE:
            secondes = min(secondes, 3 * 24 * 3600)
        return debut + timedelta(seconds=alea.randint(0, max(secondes, 1)))

    def _rapport(self, paiements, ignorees, nb_candidates: int) -> None:
        self.stdout.write(self.style.SUCCESS(
            f'{len(paiements)} paiement(s) créé(s) sur {nb_candidates} réservation(s) examinée(s).'
        ))
        for statut in (Paiement.Statut.ACCEPTE, Paiement.Statut.EN_ATTENTE, Paiement.Statut.REFUSE):
            lignes = [p for p in paiements if p.statut == statut]
            total = sum(p._valeur for p in lignes)
            self.stdout.write(f'  {statut:<12} : {len(lignes):>3}  ({total} TND)')
        for moyen in (Paiement.Moyen.CARTE, Paiement.Moyen.VIREMENT, Paiement.Moyen.ESPECES):
            n = sum(1 for p in paiements if p.moyen == moyen)
            self.stdout.write(f'  {moyen:<12} : {n}')
        self.stdout.write(
            f'  sans paiement (annulées / non initiées) : {ignorees["sans_paiement"]}'
        )
        if ignorees['montant_nul']:
            self.stdout.write(f'  ignorées (montant nul) : {ignorees["montant_nul"]}')
        encaisse = sum(p._valeur for p in paiements if p.statut == Paiement.Statut.ACCEPTE)
        self.stdout.write(self.style.SUCCESS(f'  Chiffre d’affaires encaissé : {encaisse} TND'))