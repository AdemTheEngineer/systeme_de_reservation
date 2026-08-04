"""Serializers DRF — validation de format uniquement, aucune règle métier."""

from __future__ import annotations

from rest_framework import serializers

from apps.reservations.infrastructure.models import CreneauSlot, EspaceCoworking


class SalleSerializer(serializers.ModelSerializer):
    class Meta:
        model = EspaceCoworking
        fields = (
            'id_espace',
            'nom',
            'type_espace',
            'capacite',
            'tarif_horaire',
            'disponible',
            'localisation',
            'id_gestionnaire',
            'equipements',
            'date_creation',
        )
        read_only_fields = ('id_espace', 'date_creation')


class CreneauSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreneauSlot
        fields = ('id', 'espace', 'date', 'heure_debut', 'heure_fin', 'statut')
        read_only_fields = ('id', 'statut')


class CreerReservationSerializer(serializers.Serializer):
    creneau = serializers.UUIDField()


class ReservationSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    salle_id = serializers.UUIDField()
    membre_id = serializers.UUIDField()
    date = serializers.DateField()
    heure_debut = serializers.TimeField()
    heure_fin = serializers.TimeField()
    statut = serializers.CharField()
    acompte = serializers.DecimalField(max_digits=10, decimal_places=2)
    devise = serializers.CharField()
    paiement_id = serializers.UUIDField(allow_null=True)
    date_creation = serializers.DateTimeField()
    date_modification = serializers.DateTimeField()


class DisponibiliteQuerySerializer(serializers.Serializer):
    date = serializers.DateField()
    heure_debut = serializers.TimeField()
    heure_fin = serializers.TimeField()


class SalleDisponibleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    nom = serializers.CharField()
    capacite = serializers.IntegerField()
    tarif_horaire = serializers.DecimalField(max_digits=8, decimal_places=2)
    devise = serializers.CharField()


class PeriodeQuerySerializer(serializers.Serializer):
    debut = serializers.DateField()
    fin = serializers.DateField()

    def validate(self, attrs):
        if attrs['fin'] < attrs['debut']:
            raise serializers.ValidationError("'fin' doit être postérieure ou égale à 'debut'.")
        return attrs


class TauxOccupationSerializer(serializers.Serializer):
    salle_id = serializers.UUIDField()
    nom = serializers.CharField()
    heures_reservees = serializers.DecimalField(max_digits=10, decimal_places=2)
    heures_disponibles = serializers.DecimalField(max_digits=10, decimal_places=2)
    taux = serializers.DecimalField(max_digits=6, decimal_places=4)


class RevenuPeriodeSerializer(serializers.Serializer):
    nombre_reservations = serializers.IntegerField()
    somme_acomptes = serializers.DecimalField(max_digits=12, decimal_places=2)
    devise = serializers.CharField()


class DashboardKPISerializer(serializers.Serializer):
    periode_debut = serializers.DateField()
    periode_fin = serializers.DateField()
    occupation = TauxOccupationSerializer(many=True)
    revenu = RevenuPeriodeSerializer()
