"""Mappers Entity (domaine) <-> Modèle ORM (infrastructure).

Le domaine et l'ORM Django sont deux objets distincts : c'est ici, et
uniquement ici, que la traduction a lieu. Aucune Entity n'hérite de
`models.Model`.

Réconciliations :
- `Reservation.acompte` (domaine) <-> `Reservation.montant_total` (colonne) :
  même grandeur métier sous deux noms différents (EF-10 calcule cet
  acompte comme durée × tarif_horaire, exactement ce que représente
  `montant_total`) — pas de perte d'information, simple traduction de nom.
- `Salle` n'a pas de méthode d'écriture ici : aucun use case ne crée/modifie
  une salle (`SalleRepository` n'a qu'un `get_by_id`) — seul `to_domain`
  est donc nécessaire.
- `Reservation.paiement_id` (domaine) n'a PAS de colonne dédiée : c'est
  `paiements.Paiement.reservation` (OneToOneField, `related_name='paiement'`)
  qui porte la relation, dans l'autre sens, pour éviter une dépendance
  circulaire entre apps. Le mapper lit la relation inverse.
"""

from __future__ import annotations

from datetime import date as date_type
from datetime import datetime
from datetime import time as time_type
from datetime import timezone as dt_timezone

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone as django_timezone

from apps.reservations.domain.entities import Reservation as ReservationEntity
from apps.reservations.domain.entities import Salle as SalleEntity
from apps.reservations.domain.enums import StatutReservation, StatutSalle
from apps.reservations.domain.value_objects import Creneau, Montant
from apps.reservations.infrastructure.models import EspaceCoworking as EspaceCoworkingModel
from apps.reservations.infrastructure.models import Reservation as ReservationModel


class SalleMapper:
    @staticmethod
    def to_domain(model: EspaceCoworkingModel) -> SalleEntity:
        return SalleEntity(
            id=model.id_espace,
            nom=model.nom,
            capacite=model.capacite,
            equipements=model.equipements,
            tarif_horaire=Montant(model.tarif_horaire),
            statut=StatutSalle.ACTIVE if model.disponible else StatutSalle.INACTIVE,
            date_creation=model.date_creation,
        )


class ReservationMapper:
    @staticmethod
    def to_domain(model: ReservationModel) -> ReservationEntity:
        debut = django_timezone.localtime(model.date_debut, dt_timezone.utc)
        fin = django_timezone.localtime(model.date_fin, dt_timezone.utc)
        creneau = Creneau(date=debut.date(), heure_debut=debut.time(), heure_fin=fin.time())

        return ReservationEntity(
            id=model.id_reservation,
            creneau=creneau,
            statut=StatutReservation(model.statut),
            acompte=Montant(model.montant_total),
            membre_id=model.membre_id,
            salle_id=model.espace_id,
            paiement_id=_id_paiement_lie(model),
            date_creation=model.date_creation,
            date_modification=model.date_modification,
        )

    @staticmethod
    def to_model(entity: ReservationEntity, model: ReservationModel | None = None) -> ReservationModel:
        """Traduit l'Entity vers le modèle ORM. Si `model` est fourni (mise à
        jour d'une ligne existante), ses champs sont mis à jour en place ;
        sinon une nouvelle instance non sauvegardée est créée."""
        if model is None:
            model = ReservationModel(id_reservation=entity.id)

        model.date_debut = _combine_utc(entity.creneau.date, entity.creneau.heure_debut)
        model.date_fin = _combine_utc(entity.creneau.date, entity.creneau.heure_fin)
        model.statut = entity.statut.value
        model.montant_total = entity.acompte.valeur
        model.espace_id = entity.salle_id
        model.membre_id = entity.membre_id
        return model


def _id_paiement_lie(model: ReservationModel):
    """Lit `paiement_id` via la relation inverse `paiements.Paiement.reservation`."""
    try:
        return model.paiement.id
    except ObjectDoesNotExist:
        return None


def _combine_utc(date_: date_type, time_: time_type) -> datetime:
    return datetime.combine(date_, time_, tzinfo=dt_timezone.utc)
