"""Seed du contexte support Identité — jeu de données tunisien.

Crée 100 utilisateurs par défaut (90 Membres + 10 Gestionnaires), avec noms,
prénoms et numéros de téléphone tunisiens réalistes.

Usage :
    uv run python manage.py seed_identite
    uv run python manage.py seed_identite --membres 90 --gestionnaires 10
    uv run python manage.py seed_identite --password 'Coworking#2026'
    uv run python manage.py seed_identite --flush          # supprime le seed
    uv run python manage.py seed_identite --flush --membres 0 --gestionnaires 0
"""

from __future__ import annotations

import random
import unicodedata

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.identite.models import Gestionnaire, Membre

Utilisateur = get_user_model()

# --- Jeu de données tunisien -------------------------------------------------

PRENOMS_M = (
    'Mohamed', 'Ahmed', 'Ali', 'Youssef', 'Aymen', 'Bilel', 'Chokri', 'Hamza',
    'Khaled', 'Mehdi', 'Nizar', 'Omar', 'Rami', 'Sami', 'Seif', 'Skander',
    'Tarek', 'Wassim', 'Yassine', 'Zied', 'Anis', 'Fares', 'Hatem', 'Marouane',
    'Oussama', 'Slim', 'Amine', 'Firas', 'Nader', 'Walid', 'Iheb', 'Ghassen',
    'Kais', 'Lotfi', 'Malek', 'Nabil', 'Riadh', 'Sofiene', 'Taieb', 'Hedi',
)

PRENOMS_F = (
    'Amira', 'Asma', 'Ons', 'Rania', 'Sarra', 'Salma', 'Ines', 'Nour', 'Yosra',
    'Mariem', 'Hela', 'Emna', 'Feriel', 'Ghada', 'Imen', 'Jihene', 'Khaoula',
    'Leila', 'Manel', 'Nesrine', 'Olfa', 'Rim', 'Sana', 'Sonia', 'Takoua',
    'Wafa', 'Yasmine', 'Zeineb', 'Dorra', 'Hiba', 'Chaima', 'Meriem', 'Nada',
    'Syrine', 'Amani', 'Maha', 'Sirine', 'Aya', 'Nourhene', 'Fatma',
)

NOMS = (
    'Ben Salah', 'Ben Amor', 'Ben Youssef', 'Ben Hassine', 'Ben Romdhane',
    'Bouazizi', 'Bouhlel', 'Baccouche', 'Chaabane', 'Chebbi', 'Cherif',
    'Dridi', 'Ferchichi', 'Gharbi', 'Guesmi', 'Haddad', 'Hamdi', 'Hammami',
    'Jaziri', 'Jerbi', 'Kacem', 'Karray', 'Khelifi', 'Louati', 'Mabrouk',
    'Mansouri', 'Mejri', 'Msakni', 'Nasri', 'Ouertani', 'Rekik', 'Sassi',
    'Slimane', 'Souissi', 'Trabelsi', 'Zouari', 'Abidi', 'Aloui', 'Ammar',
    'Ayari', 'Belhadj', 'Bouzid', 'Chouchane', 'Dhaouadi', 'Fakhfakh',
    'Ghribi', 'Hachicha', 'Jelassi', 'Kammoun', 'Laabidi', 'Maaloul',
    'Nefzi', 'Ounalli', 'Rhaiem', 'Saidi', 'Tounsi', 'Werghi', 'Yahyaoui',
)

# Préfixes mobiles tunisiens réellement attribués (Ooredoo / Orange / TT).
PREFIXES_MOBILES = (
    '20', '21', '22', '23', '24', '25', '26', '27', '28', '29',
    '50', '51', '52', '53', '54', '55', '56', '58',
    '90', '91', '92', '93', '94', '95', '96', '97', '98', '99',
)

# Domaines réservés par la RFC 2606 : aucun risque d'écrire à une vraie personne.
# Remplacer par 'gmail.com' / 'topnet.tn' si un rendu plus "réel" est souhaité.
DOMAINES = ('example.com', 'example.net', 'example.org')

MOT_DE_PASSE_DEFAUT = 'Coworking#2026'
GRAINE_ALEATOIRE = 2026  # rend le seed reproductible à l'identique


def _ascii(valeur: str) -> str:
    """'Béchir Ben Salah' -> 'bechir.bensalah' (sûr pour un email)."""
    sans_accent = unicodedata.normalize('NFKD', valeur).encode('ascii', 'ignore').decode()
    return ''.join(c for c in sans_accent.lower() if c.isalnum())


class Command(BaseCommand):
    help = "Peuple le contexte Identité avec 100 utilisateurs tunisiens de démonstration."

    def add_arguments(self, parser):
        parser.add_argument('--membres', type=int, default=90, help='Nombre de membres (défaut : 90).')
        parser.add_argument('--gestionnaires', type=int, default=10, help='Nombre de gestionnaires (défaut : 10).')
        parser.add_argument('--password', type=str, default=MOT_DE_PASSE_DEFAUT, help='Mot de passe commun.')
        parser.add_argument('--flush', action='store_true', help='Supprime les utilisateurs du seed avant insertion.')
        parser.add_argument('--seed', type=int, default=GRAINE_ALEATOIRE, help='Graine aléatoire.')

    @transaction.atomic
    def handle(self, *args, **options):
        nb_membres: int = options['membres']
        nb_gestionnaires: int = options['gestionnaires']
        if nb_membres < 0 or nb_gestionnaires < 0:
            raise CommandError('Les effectifs doivent être positifs.')

        alea = random.Random(options['seed'])

        if options['flush']:
            supprimes, _ = Utilisateur.objects.filter(
                email__endswith='.seed@example.com'
            ).delete()
            # Les profils Membre/Gestionnaire partent en cascade (on_delete=CASCADE).
            self.stdout.write(self.style.WARNING(f'{supprimes} objet(s) supprimé(s).'))

        total = nb_membres + nb_gestionnaires
        if total == 0:
            self.stdout.write(self.style.SUCCESS('Rien à insérer.'))
            return

        # Un seul hash calculé pour tout le lot : ~100x plus rapide qu'un set_password
        # par utilisateur. Acceptable pour des données de démonstration uniquement.
        hash_commun = make_password(options['password'])

        emails_existants = set(Utilisateur.objects.values_list('email', flat=True))
        utilisateurs: list[Utilisateur] = []
        emails_du_lot: set[str] = set()

        for index in range(total):
            est_gestionnaire = index >= nb_membres
            prenom = alea.choice(PRENOMS_M if alea.random() < 0.5 else PRENOMS_F)
            nom = alea.choice(NOMS)

            # Email déterministe et garanti unique, suffixé pour rester identifiable
            # comme donnée de seed (utilisé par --flush).
            base = f'{_ascii(prenom)}.{_ascii(nom)}'
            email = f'{base}.seed@{DOMAINES[0]}'
            compteur = 1
            while email in emails_existants or email in emails_du_lot:
                compteur += 1
                email = f'{base}{compteur}.seed@{DOMAINES[0]}'
            emails_du_lot.add(email)

            telephone = f'+216 {alea.choice(PREFIXES_MOBILES)} {alea.randint(100, 999)} {alea.randint(100, 999)}'

            utilisateurs.append(
                Utilisateur(
                    email=email,
                    first_name=prenom,
                    last_name=nom,
                    telephone=telephone,
                    password=hash_commun,
                    is_active=True,
                    # Les gestionnaires accèdent à l'admin Django ; pas les membres.
                    is_staff=est_gestionnaire,
                    is_superuser=False,
                )
            )

        crees = Utilisateur.objects.bulk_create(utilisateurs, batch_size=200)

        Membre.objects.bulk_create(
            [Membre(utilisateur=u) for u in crees[:nb_membres]], batch_size=200
        )
        Gestionnaire.objects.bulk_create(
            [Gestionnaire(utilisateur=u) for u in crees[nb_membres:]], batch_size=200
        )

        self.stdout.write(self.style.SUCCESS(
            f'{nb_membres} membre(s) et {nb_gestionnaires} gestionnaire(s) créés — '
            f'{total} utilisateur(s) au total.'
        ))
        if crees:
            self.stdout.write(f'  Exemple membre        : {crees[0].email}')
            if nb_gestionnaires:
                self.stdout.write(f'  Exemple gestionnaire  : {crees[nb_membres].email}')
            self.stdout.write(f'  Mot de passe commun   : {options["password"]}')