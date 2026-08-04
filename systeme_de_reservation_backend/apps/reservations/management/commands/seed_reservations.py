"""Seed du contexte Réservation — espaces, créneaux et réservations (Tunisie).

Ordre d'exécution du projet :
    1. seed_identite      (membres + gestionnaires)
    2. seed_reservations  (ce fichier)
    3. seed_paiements

Contrainte structurante : la migration 0002 pose un EXCLUDE USING gist qui
interdit à deux réservations CONFIRMEE de se chevaucher sur un même espace.
Les créneaux sont donc générés DISJOINTS par construction (et confrontés aux
réservations confirmées déjà en base), plutôt qu'insérés au hasard puis
retentés sur IntegrityError.

Usage :
    uv run python manage.py seed_reservations
    uv run python manage.py seed_reservations --reservations 150
    uv run python manage.py seed_reservations --flush            # reset du seed
    uv run python manage.py seed_reservations --flush --reservations 0
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.apps import apps as django_apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.identite.models import Gestionnaire, Membre
from apps.reservations.infrastructure.models import (
    CreneauSlot,
    EspaceCoworking,
    Reservation,
)

# --- Identité déterministe du jeu de données ---------------------------------

# Namespace fixe : les id_espace sont dérivés du nom par uuid5, donc stables
# d'une exécution à l'autre. C'est ce qui rend --flush chirurgical (il ne peut
# toucher que les 12 espaces ci-dessous) et le seed rejouable.
NAMESPACE_SEED = uuid.UUID('1e5a4d2c-7b30-5f18-9c64-3a0d8e21f7b5')
GRAINE_ALEATOIRE = 2026

JOURS_PASSES = 45
JOURS_FUTURS = 30
HEURE_OUVERTURE = 8
HEURE_FERMETURE = 20
DUREES_POSSIBLES = (1, 1, 2, 2, 2, 3, 4)  # heures ; 2h le plus fréquent

# --- Catalogue d'espaces (tarifs horaires TND réalistes) ---------------------

CATALOGUE_ESPACES = (
    # (nom, type, capacité, tarif_horaire, localisation, équipements)
    ('Open Space Lac 2', 'OPEN_SPACE', 40, '9.00', 'Les Berges du Lac 2, Tunis',
     'Wifi fibre, café illimité, casiers, imprimante'),
    ('Open Space Centre Urbain Nord', 'OPEN_SPACE', 32, '8.00', 'Centre Urbain Nord, Tunis',
     'Wifi fibre, espace détente, parking'),
    ('Open Space Sousse Corniche', 'OPEN_SPACE', 24, '7.50', 'Corniche, Sousse',
     'Wifi, terrasse, café'),
    ('Open Space Sfax Centre', 'OPEN_SPACE', 20, '7.00', 'Avenue Habib Bourguiba, Sfax',
     'Wifi, imprimante, cuisine partagée'),
    ('Bureau Privé Marsa 1', 'BUREAU_PRIVE', 4, '26.00', 'La Marsa, Tunis',
     'Bureau fermé, écran 27", climatisation, casier'),
    ('Bureau Privé Marsa 2', 'BUREAU_PRIVE', 6, '32.00', 'La Marsa, Tunis',
     'Bureau fermé, double écran, tableau blanc'),
    ('Bureau Privé Ariana', 'BUREAU_PRIVE', 3, '22.00', 'Ariana Ville, Ariana',
     'Bureau fermé, wifi dédié, parking'),
    ('Bureau Privé Lac 1', 'BUREAU_PRIVE', 8, '38.00', 'Les Berges du Lac 1, Tunis',
     'Bureau fermé, visioconférence, secrétariat'),
    ('Salle Carthage', 'SALLE_REUNION', 12, '55.00', 'Les Berges du Lac 2, Tunis',
     'Vidéoprojecteur, paperboard, visioconférence, café'),
    ('Salle Kairouan', 'SALLE_REUNION', 8, '45.00', 'Centre Urbain Nord, Tunis',
     'Écran 65", paperboard, wifi'),
    ('Salle Djerba', 'SALLE_REUNION', 20, '80.00', 'Corniche, Sousse',
     'Sonorisation, vidéoprojecteur, restauration sur demande'),
    ('Salle Tozeur', 'SALLE_REUNION', 6, '40.00', 'Avenue Habib Bourguiba, Sfax',
     'Écran, tableau blanc, wifi'),
)

# Répartition des statuts : le passé est tranché (confirmé ou annulé),
# le futur laisse une part de réservations encore en attente de paiement.
POIDS_STATUT_PASSE = ((Reservation.Statut.CONFIRMEE, 72),
                      (Reservation.Statut.ANNULEE, 20),
                      (Reservation.Statut.EN_ATTENTE, 8))
POIDS_STATUT_FUTUR = ((Reservation.Statut.CONFIRMEE, 55),
                      (Reservation.Statut.EN_ATTENTE, 35),
                      (Reservation.Statut.ANNULEE, 10))


def _id_espace(nom: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE_SEED, f'espace:{nom}')


def _tirage(alea: random.Random, table) -> str:
    return alea.choices([v for v, _ in table], weights=[p for _, p in table], k=1)[0]


class Command(BaseCommand):
    help = "Peuple le contexte Réservation : espaces, créneaux et réservations."

    def add_arguments(self, parser):
        parser.add_argument('--reservations', type=int, default=100,
                            help='Nombre de réservations à créer (défaut : 100).')
        parser.add_argument('--creneaux-libres', type=int, default=60,
                            help='Créneaux DISPONIBLE à venir, non réservés (défaut : 60).')
        parser.add_argument('--flush', action='store_true',
                            help='Supprime espaces/créneaux/réservations du seed avant insertion.')
        parser.add_argument('--seed', type=int, default=GRAINE_ALEATOIRE,
                            help='Graine aléatoire (reproductibilité).')

    @transaction.atomic
    def handle(self, *args, **options):
        nb_reservations: int = options['reservations']
        nb_libres: int = options['creneaux_libres']
        if nb_reservations < 0 or nb_libres < 0:
            raise CommandError('Les effectifs doivent être positifs.')

        alea = random.Random(options['seed'])
        ids_seed = [_id_espace(nom) for nom, *_ in CATALOGUE_ESPACES]

        if options['flush']:
            self._flush(ids_seed)

        if nb_reservations == 0 and nb_libres == 0:
            self.stdout.write(self.style.SUCCESS('Rien à insérer.'))
            return

        espaces = self._creer_espaces(alea)
        self.stdout.write(self.style.SUCCESS(f'{len(espaces)} espace(s) en base.'))

        if nb_reservations == 0 and nb_libres == 0:
            return

        membres = list(Membre.objects.only('id').order_by('id'))
        if not membres:
            raise CommandError(
                'Aucun Membre en base. Lancez d’abord : '
                'uv run python manage.py seed_identite'
            )

        pool = self._construire_creneaux_disjoints(alea, espaces)
        besoin = nb_reservations + nb_libres
        if len(pool) < besoin:
            raise CommandError(
                f'Seulement {len(pool)} créneau(x) libre(s) disponible(s) pour {besoin} demandé(s). '
                'Élargissez la fenêtre ou réduisez --reservations.'
            )

        alea.shuffle(pool)
        pour_reservations = pool[:nb_reservations]
        pour_libres = [c for c in pool[nb_reservations:nb_reservations + nb_libres]
                       if c['debut'] > timezone.now()]

        creneaux, reservations = self._construire(alea, pour_reservations, membres)
        libres = [
            CreneauSlot(espace=c['espace'], date=c['debut'].date(),
                        heure_debut=c['debut'].time(), heure_fin=c['fin'].time(),
                        statut=CreneauSlot.Statut.DISPONIBLE)
            for c in pour_libres
        ]

        CreneauSlot.objects.bulk_create(creneaux + libres, batch_size=200)
        crees = Reservation.objects.bulk_create(reservations, batch_size=200)

        # date_creation est auto_now_add : sans retouche, les 100 lignes
        # porteraient le même horodatage et tout KPI temporel serait plat.
        # bulk_update n'applique pas auto_now_add/auto_now, on peut l'écraser.
        maintenant = timezone.now()
        for reservation in crees:
            anticipation = timedelta(days=alea.randint(1, 21), minutes=alea.randint(0, 1439))
            reservation.date_creation = min(reservation.date_debut - anticipation, maintenant)
        Reservation.objects.bulk_update(crees, ['date_creation'], batch_size=200)

        self._rapport(crees, libres, maintenant)

    # --- Étapes -------------------------------------------------------------

    def _flush(self, ids_seed: list[uuid.UUID]) -> None:
        """Supprime dans l'ordre imposé par les on_delete=RESTRICT :
        paiements → réservations → espaces (les créneaux partent en CASCADE)."""
        reservations = Reservation.objects.filter(espace_id__in=ids_seed)

        Paiement = django_apps.get_model('paiements', 'Paiement')
        n_paiements, _ = Paiement.objects.filter(reservation__in=reservations).delete()
        if n_paiements:
            self.stdout.write(self.style.WARNING(
                f'{n_paiements} paiement(s) rattaché(s) supprimé(s) (RESTRICT).'
            ))

        n_reservations, _ = reservations.delete()
        n_espaces, _ = EspaceCoworking.objects.filter(id_espace__in=ids_seed).delete()
        self.stdout.write(self.style.WARNING(
            f'{n_reservations} réservation(s) et {n_espaces} espace(s) supprimé(s).'
        ))

    def _creer_espaces(self, alea: random.Random) -> list[EspaceCoworking]:
        gestionnaires = list(Gestionnaire.objects.values_list('id', flat=True))
        if not gestionnaires:
            self.stdout.write(self.style.WARNING(
                'Aucun Gestionnaire : id_gestionnaire sera un UUID orphelin.'
            ))

        espaces: list[EspaceCoworking] = []
        for nom, type_espace, capacite, tarif, localisation, equipements in CATALOGUE_ESPACES:
            espace, _ = EspaceCoworking.objects.update_or_create(
                id_espace=_id_espace(nom),
                defaults={
                    'nom': nom,
                    'type_espace': type_espace,
                    'capacite': capacite,
                    'tarif_horaire': Decimal(tarif),
                    'disponible': True,
                    'localisation': localisation,
                    'id_gestionnaire': alea.choice(gestionnaires) if gestionnaires else uuid.uuid4(),
                    'equipements': equipements,
                },
            )
            espaces.append(espace)
        return espaces

    def _construire_creneaux_disjoints(self, alea, espaces) -> list[dict]:
        """Génère, par espace, des plages horaires sans aucun recouvrement,
        puis élimine celles qui heurteraient une réservation CONFIRMEE déjà
        en base (l'EXCLUDE gist ne tolère aucun chevauchement)."""
        tz = timezone.get_current_timezone()
        aujourd_hui = timezone.localdate()
        pool: list[dict] = []

        for espace in espaces:
            occupes = list(
                Reservation.objects.filter(
                    espace=espace, statut=Reservation.Statut.CONFIRMEE
                ).values_list('date_debut', 'date_fin')
            )

            for delta in range(-JOURS_PASSES, JOURS_FUTURS + 1):
                jour = aujourd_hui + timedelta(days=delta)
                if jour.weekday() == 6:  # dimanche fermé
                    continue

                heure = HEURE_OUVERTURE
                while heure < HEURE_FERMETURE:
                    duree = alea.choice(DUREES_POSSIBLES)
                    if heure + duree > HEURE_FERMETURE:
                        break
                    debut = timezone.make_aware(datetime.combine(jour, time(heure)), tz)
                    fin = debut + timedelta(hours=duree)

                    if not any(debut < f and d < fin for d, f in occupes):
                        pool.append({'espace': espace, 'debut': debut, 'fin': fin, 'heures': duree})

                    # Pas inter-créneaux : la pause garantit la disjonction
                    # même après tirage aléatoire des durées.
                    heure += duree + alea.choice((0, 1, 1, 2))
        return pool

    def _construire(self, alea, creneaux_choisis, membres):
        maintenant = timezone.now()
        slots: list[CreneauSlot] = []
        reservations: list[Reservation] = []

        for creneau in creneaux_choisis:
            espace: EspaceCoworking = creneau['espace']
            passe = creneau['fin'] < maintenant
            statut = _tirage(alea, POIDS_STATUT_PASSE if passe else POIDS_STATUT_FUTUR)

            slot = CreneauSlot(
                espace=espace,
                date=creneau['debut'].date(),
                heure_debut=creneau['debut'].time(),
                heure_fin=creneau['fin'].time(),
                statut=(CreneauSlot.Statut.DISPONIBLE
                        if statut == Reservation.Statut.ANNULEE
                        else CreneauSlot.Statut.RESERVE),
            )
            slots.append(slot)

            montant = (espace.tarif_horaire * creneau['heures']).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            )
            reservations.append(
                Reservation(
                    creneau_slot=slot,
                    espace=espace,
                    membre=alea.choice(membres),
                    date_debut=creneau['debut'],
                    date_fin=creneau['fin'],
                    statut=statut,
                    montant_total=montant,
                )
            )
        return slots, reservations

    def _rapport(self, reservations, libres, maintenant) -> None:
        self.stdout.write(self.style.SUCCESS(f'{len(reservations)} réservation(s) créée(s).'))
        for statut, _ in POIDS_STATUT_PASSE:
            n = sum(1 for r in reservations if r.statut == statut)
            self.stdout.write(f'  {statut:<12} : {n}')
        passees = sum(1 for r in reservations if r.date_fin < maintenant)
        self.stdout.write(f'  passées / à venir  : {passees} / {len(reservations) - passees}')
        ca = sum(r.montant_total for r in reservations
                 if r.statut == Reservation.Statut.CONFIRMEE)
        self.stdout.write(f'  CA confirmé        : {ca} TND')
        self.stdout.write(f'  créneaux DISPONIBLE : {len(libres)}')