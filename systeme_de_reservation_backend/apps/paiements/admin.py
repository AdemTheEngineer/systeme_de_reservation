from django.contrib import admin

from apps.paiements.models import Paiement


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('id', 'reservation', 'statut', 'moyen', '_valeur', '_devise', 'date_paiement')
    list_filter = ('statut', 'moyen')
