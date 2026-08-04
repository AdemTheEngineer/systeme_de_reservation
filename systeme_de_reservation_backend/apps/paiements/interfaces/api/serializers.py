from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from apps.paiements.models import Paiement


class PaiementCreateSerializer(serializers.Serializer):
    reservation = serializers.UUIDField()
    montant = serializers.DecimalField(max_digits=8, decimal_places=2, min_value=Decimal('0.01'))
    devise = serializers.CharField(max_length=3, default='TND')
    moyen = serializers.ChoiceField(choices=Paiement.Moyen.choices, default=Paiement.Moyen.CARTE)


class PaiementSerializer(serializers.ModelSerializer):
    reservation = serializers.UUIDField(source='reservation_id')
    montant = serializers.DecimalField(source='_valeur', max_digits=8, decimal_places=2, read_only=True)
    devise = serializers.CharField(source='_devise', read_only=True)

    class Meta:
        model = Paiement
        fields = ('id', 'reservation', 'montant', 'devise', 'statut', 'moyen', 'reference_externe', 'date_paiement')
        read_only_fields = fields
