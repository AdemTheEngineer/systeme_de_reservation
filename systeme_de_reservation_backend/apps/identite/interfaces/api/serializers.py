from __future__ import annotations

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.identite.models import Gestionnaire, Membre, Utilisateur


class LoginSerializer(TokenObtainPairSerializer):
    """`POST /auth/login {email, mot_de_passe}` — champ `mot_de_passe` au lieu de `password`.

    Renommer la clé du champ (`field_name`) suffit : son `source` reste
    `'password'` (fixé au premier `bind()`), donc `to_internal_value` peuple
    déjà `attrs['password']` correctement à partir de l'entrée `mot_de_passe`
    — pas besoin de remapper quoi que ce soit dans `validate()`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['mot_de_passe'] = self.fields.pop('password')


class UtilisateurMeSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = Utilisateur
        fields = ('id', 'email', 'first_name', 'last_name', 'telephone', 'role')

    def get_role(self, obj: Utilisateur) -> str:
        if hasattr(obj, 'gestionnaire'):
            return 'gestionnaire'
        if hasattr(obj, 'membre'):
            return 'membre'
        return 'aucun'


class MembreSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='utilisateur.email')
    telephone = serializers.CharField(source='utilisateur.telephone', required=False, allow_blank=True)
    mot_de_passe = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Membre
        fields = ('id', 'email', 'telephone', 'mot_de_passe', 'date_creation')
        read_only_fields = ('id', 'date_creation')

    def create(self, validated_data: dict) -> Membre:
        utilisateur_data = validated_data.pop('utilisateur')
        mot_de_passe = validated_data.pop('mot_de_passe', None)
        utilisateur = Utilisateur.objects.create_user(password=mot_de_passe, **utilisateur_data)
        return Membre.objects.create(utilisateur=utilisateur, **validated_data)

    def update(self, instance: Membre, validated_data: dict) -> Membre:
        utilisateur_data = validated_data.pop('utilisateur', {})
        mot_de_passe = validated_data.pop('mot_de_passe', None)
        for field, value in utilisateur_data.items():
            setattr(instance.utilisateur, field, value)
        if mot_de_passe:
            instance.utilisateur.set_password(mot_de_passe)
        instance.utilisateur.save()
        return instance


class GestionnaireSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='utilisateur.email')
    telephone = serializers.CharField(source='utilisateur.telephone', required=False, allow_blank=True)
    mot_de_passe = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Gestionnaire
        fields = ('id', 'email', 'telephone', 'mot_de_passe', 'date_creation')
        read_only_fields = ('id', 'date_creation')

    def create(self, validated_data: dict) -> Gestionnaire:
        utilisateur_data = validated_data.pop('utilisateur')
        mot_de_passe = validated_data.pop('mot_de_passe', None)
        utilisateur = Utilisateur.objects.create_user(password=mot_de_passe, **utilisateur_data)
        return Gestionnaire.objects.create(utilisateur=utilisateur, **validated_data)

    def update(self, instance: Gestionnaire, validated_data: dict) -> Gestionnaire:
        utilisateur_data = validated_data.pop('utilisateur', {})
        mot_de_passe = validated_data.pop('mot_de_passe', None)
        for field, value in utilisateur_data.items():
            setattr(instance.utilisateur, field, value)
        if mot_de_passe:
            instance.utilisateur.set_password(mot_de_passe)
        instance.utilisateur.save()
        return instance
