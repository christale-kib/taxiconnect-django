# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class BrandAmbassadors(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=255)
    telephone = models.CharField(unique=True, max_length=20)
    password_hash = models.CharField(max_length=255)
    niveau = models.CharField(max_length=50, blank=True, null=True)
    rang = models.IntegerField(blank=True, null=True)
    total_chauffeurs = models.IntegerField(blank=True, null=True)
    total_passagers = models.IntegerField(blank=True, null=True)
    chauffeurs_actifs = models.IntegerField(blank=True, null=True)
    commission_mois = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    commission_totale = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    serie_jours = models.IntegerField(blank=True, null=True)
    photo_url = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'brand_ambassadors'


class Challenges(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=50)
    objectif_type = models.CharField(max_length=50, blank=True, null=True)
    objectif_valeur = models.IntegerField()
    recompense_type = models.CharField(max_length=50, blank=True, null=True)
    recompense_valeur = models.CharField(max_length=200, blank=True, null=True)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    actif = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'challenges'


class Chauffeurs(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING)
    station = models.ForeignKey('Stations', models.DO_NOTHING, blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255, blank=True, null=True)
    telephone = models.CharField(unique=True, max_length=20)
    email = models.CharField(max_length=255, blank=True, null=True)
    vehicule_immatriculation = models.CharField(unique=True, max_length=50)
    vehicule_marque = models.CharField(max_length=100)
    vehicule_modele = models.CharField(max_length=100, blank=True, null=True)
    vehicule_couleur = models.CharField(max_length=50, blank=True, null=True)
    vehicule_annee = models.IntegerField(blank=True, null=True)
    photo_profil_url = models.TextField(blank=True, null=True)
    photo_id_url = models.TextField(blank=True, null=True)
    total_courses = models.IntegerField(blank=True, null=True)
    courses_mois = models.IntegerField(blank=True, null=True)
    note_moyenne = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True)
    statut = models.CharField(max_length=20, blank=True, null=True)
    date_activation = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'chauffeurs'


class Commissions(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING)
    type = models.CharField(max_length=50)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    recrue_type = models.CharField(max_length=20, blank=True, null=True)
    recrue_id = models.IntegerField(blank=True, null=True)
    statut = models.CharField(max_length=20, blank=True, null=True)
    date_validation = models.DateTimeField(blank=True, null=True)
    date_paiement = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'commissions'


class Notifications(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING)
    titre = models.CharField(max_length=200)
    message = models.TextField()
    type = models.CharField(max_length=50, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    lu = models.IntegerField(blank=True, null=True)
    date_lecture = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'notifications'


class ParticipationsChallenges(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING)
    challenge = models.ForeignKey(Challenges, models.DO_NOTHING)
    progression = models.IntegerField(blank=True, null=True)
    completed = models.IntegerField(blank=True, null=True)
    date_completion = models.DateTimeField(blank=True, null=True)
    recompense_recue = models.IntegerField(blank=True, null=True)
    date_recompense = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'participations_challenges'
        unique_together = (('ba', 'challenge'),)


class Passagers(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING, blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(unique=True, max_length=20)
    email = models.CharField(max_length=255, blank=True, null=True)
    photo_profil_url = models.TextField(blank=True, null=True)
    photo_id_url = models.TextField(blank=True, null=True)
    total_courses = models.IntegerField(blank=True, null=True)
    courses_mois = models.IntegerField(blank=True, null=True)
    montant_total_depense = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    statut = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'passagers'


class Sessions(models.Model):
    ba = models.ForeignKey(BrandAmbassadors, models.DO_NOTHING)
    token = models.CharField(unique=True, max_length=500)
    device_type = models.CharField(max_length=50, blank=True, null=True)
    device_name = models.CharField(max_length=200, blank=True, null=True)
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField()
    last_activity = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'sessions'


class Stations(models.Model):
    nom = models.CharField(max_length=200)
    ville = models.CharField(max_length=100)
    quartier = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    nombre_chauffeurs = models.IntegerField(blank=True, null=True)
    actif = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'stations'


class Transactions(models.Model):
    chauffeur = models.ForeignKey(Chauffeurs, models.DO_NOTHING)
    passager = models.ForeignKey(Passagers, models.DO_NOTHING, blank=True, null=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    commission_taux = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    commission_montant = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    depart_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    depart_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    arrivee_latitude = models.DecimalField(max_digits=10, decimal_places=8, blank=True, null=True)
    arrivee_longitude = models.DecimalField(max_digits=11, decimal_places=8, blank=True, null=True)
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    statut = models.CharField(max_length=20, blank=True, null=True)
    methode_paiement = models.CharField(max_length=50, blank=True, null=True)
    reference_paiement = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'transactions'
