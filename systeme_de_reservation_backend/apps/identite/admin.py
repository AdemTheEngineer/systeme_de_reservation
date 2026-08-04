from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.identite.models import Gestionnaire, Membre, Utilisateur


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    ordering = ('email',)
    list_display = ('email', 'telephone', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'telephone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = ((None, {'classes': ('wide',), 'fields': ('email', 'password1', 'password2')}),)
    search_fields = ('email',)


@admin.register(Membre)
class MembreAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur')


@admin.register(Gestionnaire)
class GestionnaireAdmin(admin.ModelAdmin):
    list_display = ('id', 'utilisateur')
