from django.contrib import admin

from apps.reservations.infrastructure.models import EspaceCoworking, Reservation


@admin.register(EspaceCoworking)
class EspaceCoworkingAdmin(admin.ModelAdmin):
    list_display = ('id_espace', 'nom', 'type_espace', 'capacite', 'tarif_horaire', 'disponible')
    list_filter = ('type_espace', 'disponible')
    search_fields = ('nom',)


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id_reservation', 'espace', 'statut', 'date_debut', 'date_fin', 'montant_total')
    list_filter = ('statut',)
    date_hierarchy = 'date_debut'
