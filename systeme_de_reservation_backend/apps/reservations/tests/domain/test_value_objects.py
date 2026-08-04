from datetime import date, time
from decimal import Decimal

import pytest

from apps.reservations.domain.exceptions import CreneauInvalideError, MontantInvalideError
from apps.reservations.domain.value_objects import Creneau, Montant


class TestCreneau:
    def test_creation_valide(self):
        c = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        assert c.heure_debut < c.heure_fin

    def test_heure_debut_egale_heure_fin_leve_exception(self):
        with pytest.raises(CreneauInvalideError):
            Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(9, 0))

    def test_heure_debut_apres_heure_fin_leve_exception(self):
        with pytest.raises(CreneauInvalideError):
            Creneau(date=date(2026, 7, 20), heure_debut=time(11, 0), heure_fin=time(9, 0))

    def test_chevauche_creneaux_qui_se_recouvrent(self):
        c1 = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        c2 = Creneau(date=date(2026, 7, 20), heure_debut=time(10, 0), heure_fin=time(12, 0))
        assert c1.chevauche(c2)
        assert c2.chevauche(c1)

    def test_chevauche_creneaux_contigus_ne_se_recouvrent_pas(self):
        c1 = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        c2 = Creneau(date=date(2026, 7, 20), heure_debut=time(11, 0), heure_fin=time(13, 0))
        assert not c1.chevauche(c2)

    def test_chevauche_dates_differentes_ne_se_recouvrent_jamais(self):
        c1 = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        c2 = Creneau(date=date(2026, 7, 21), heure_debut=time(9, 0), heure_fin=time(11, 0))
        assert not c1.chevauche(c2)

    def test_egalite_par_valeur(self):
        c1 = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        c2 = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        assert c1 == c2

    def test_immutable(self):
        c = Creneau(date=date(2026, 7, 20), heure_debut=time(9, 0), heure_fin=time(11, 0))
        with pytest.raises(Exception):
            c.heure_debut = time(10, 0)


class TestChevaucheMatrice:
    """Matrice complète de recouvrement pour `Creneau.chevauche` — la plage
    est semi-ouverte [debut, fin) : les bords qui se touchent ne se
    chevauchent pas."""

    JOUR = date(2026, 7, 20)

    @pytest.mark.parametrize(
        ('a', 'b', 'attendu'),
        [
            # Recouvrement partiel (avant / après)
            ((time(9, 0), time(11, 0)), (time(10, 0), time(12, 0)), True),
            ((time(10, 0), time(12, 0)), (time(9, 0), time(11, 0)), True),
            # Identiques
            ((time(9, 0), time(11, 0)), (time(9, 0), time(11, 0)), True),
            # Inclusion stricte (l'un contient l'autre)
            ((time(9, 0), time(12, 0)), (time(10, 0), time(11, 0)), True),
            ((time(10, 0), time(11, 0)), (time(9, 0), time(12, 0)), True),
            # Même début ou même fin
            ((time(9, 0), time(11, 0)), (time(9, 0), time(10, 0)), True),
            ((time(9, 0), time(11, 0)), (time(10, 0), time(11, 0)), True),
            # Bords qui se touchent : pas de chevauchement
            ((time(9, 0), time(11, 0)), (time(11, 0), time(13, 0)), False),
            ((time(11, 0), time(13, 0)), (time(9, 0), time(11, 0)), False),
            # Disjoints
            ((time(9, 0), time(10, 0)), (time(11, 0), time(12, 0)), False),
            # Chevauchement d'une minute seulement
            ((time(9, 0), time(11, 0)), (time(10, 59), time(12, 0)), True),
        ],
    )
    def test_matrice(self, a, b, attendu):
        c1 = Creneau(self.JOUR, *a)
        c2 = Creneau(self.JOUR, *b)
        assert c1.chevauche(c2) is attendu
        assert c2.chevauche(c1) is attendu  # symétrie


class TestDureeHeures:
    def test_duree_entiere(self):
        c = Creneau(date(2026, 7, 20), time(9, 0), time(11, 0))
        assert c.duree_heures == Decimal('2')

    def test_duree_fractionnaire(self):
        c = Creneau(date(2026, 7, 20), time(9, 0), time(10, 30))
        assert c.duree_heures == Decimal('1.5')

    def test_acompte_fractionnaire_arrondi_half_up(self):
        """EF-10 : 1h30 × 19.99 = 29.985 → arrondi à 29.99 (ROUND_HALF_UP)
        par le VO `Montant` (jamais de flottant binaire)."""
        c = Creneau(date(2026, 7, 20), time(9, 0), time(10, 30))
        acompte = Montant(c.duree_heures * Decimal('19.99'), 'TND')
        assert acompte.valeur == Decimal('29.99')


class TestMontant:
    def test_creation_valide(self):
        m = Montant(Decimal('50.5'), 'TND')
        assert m.valeur == Decimal('50.50')

    def test_valeur_negative_leve_exception(self):
        with pytest.raises(MontantInvalideError):
            Montant(Decimal('-1'), 'TND')

    def test_valeur_zero_est_autorisee_au_niveau_value_object(self):
        m = Montant(Decimal('0'), 'TND')
        assert not m.est_strictement_positif()

    def test_devise_invalide_leve_exception(self):
        with pytest.raises(MontantInvalideError):
            Montant(Decimal('10'), 'tnd')
        with pytest.raises(MontantInvalideError):
            Montant(Decimal('10'), 'TN')

    def test_arrondi_deux_decimales(self):
        m = Montant(Decimal('10.256'), 'TND')
        assert m.valeur == Decimal('10.26')

    def test_egalite_par_valeur(self):
        assert Montant(Decimal('10'), 'TND') == Montant(Decimal('10.00'), 'TND')

    def test_addition_meme_devise(self):
        total = Montant(Decimal('10'), 'TND') + Montant(Decimal('5'), 'TND')
        assert total == Montant(Decimal('15'), 'TND')

    def test_addition_devises_differentes_leve_exception(self):
        with pytest.raises(MontantInvalideError):
            Montant(Decimal('10'), 'TND') + Montant(Decimal('5'), 'EUR')

    def test_comparaison(self):
        assert Montant(Decimal('5'), 'TND') < Montant(Decimal('10'), 'TND')

    def test_immutable(self):
        m = Montant(Decimal('10'), 'TND')
        with pytest.raises(Exception):
            m.valeur = Decimal('20')
