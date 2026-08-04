"""Test de course réel : deux confirmations concurrentes de réservations
chevauchantes ne peuvent pas toutes les deux commiter.

Deux threads (donc deux connexions PostgreSQL distinctes) tentent en même
temps de passer EN_ATTENTE → CONFIRMEE deux réservations qui se chevauchent
sur la même salle. La vérification applicative (`autres_reservations_confirmees`)
ne voit rien dans les deux cas — c'est exactement le scénario de course que
la contrainte GIST EXCLUDE doit arbitrer : le second UPDATE attend le commit
du premier puis échoue.

`transaction=True` est indispensable : chaque thread doit réellement
commiter pour que l'autre voie (ou pas) sa ligne.
"""

import threading
import uuid
from datetime import date, time
from decimal import Decimal

import pytest
from django.db import connection

from apps.identite.models import Membre, Utilisateur
from apps.reservations.domain.exceptions import ChevauchementCreneauError
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel
from apps.reservations.infrastructure.repositories import DjangoReservationRepository

pytestmark = pytest.mark.django_db(transaction=True)


def test_deux_confirmations_chevauchantes_concurrentes_une_seule_commit():
    espace = EspaceCoworkingModel.objects.create(
        nom=f'Salle {uuid.uuid4()}',
        type_espace=EspaceCoworkingModel.TypeEspace.SALLE_REUNION,
        capacite=8,
        tarif_horaire=Decimal('20.00'),
        disponible=True,
        id_gestionnaire=uuid.uuid4(),
    )
    membre = Membre.objects.create(
        utilisateur=Utilisateur.objects.create_user(email=f'{uuid.uuid4()}@test.local', password='x')
    )

    # Deux EN_ATTENTE chevauchantes : autorisé (seule CONFIRMEE bloque).
    ids = []
    for debut, fin in ((time(9, 0), time(11, 0)), (time(10, 0), time(12, 0))):
        r = ReservationModel.objects.create(
            date_debut=f'2026-08-01T{debut:%H:%M}:00+00:00',
            date_fin=f'2026-08-01T{fin:%H:%M}:00+00:00',
            statut=ReservationModel.Statut.EN_ATTENTE,
            montant_total=Decimal('40.00'),
            espace=espace,
            membre=membre,
        )
        ids.append(r.id_reservation)

    barriere = threading.Barrier(2)
    resultats: dict[uuid.UUID, str] = {}

    def confirmer(reservation_id: uuid.UUID) -> None:
        try:
            repo = DjangoReservationRepository()
            entity = repo.get_by_id(reservation_id)
            # Aucune "autre confirmée" visible à cet instant : la garde
            # applicative passe dans les deux threads — course authentique.
            entity.confirmer(uuid.uuid4())
            barriere.wait(timeout=10)
            repo.save(entity)
            resultats[reservation_id] = 'confirmee'
        except ChevauchementCreneauError:
            resultats[reservation_id] = 'conflit'
        except Exception as exc:  # échec inattendu : remonté dans l'assert final
            resultats[reservation_id] = f'erreur: {exc!r}'
        finally:
            connection.close()

    threads = [threading.Thread(target=confirmer, args=(rid,)) for rid in ids]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not any(t.is_alive() for t in threads), 'blocage : un thread n’a pas terminé'

    assert sorted(resultats.values()) == ['confirmee', 'conflit'], resultats

    confirmees = ReservationModel.objects.filter(
        espace=espace, statut=ReservationModel.Statut.CONFIRMEE
    ).count()
    assert confirmees == 1
