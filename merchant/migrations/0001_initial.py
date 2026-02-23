from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Merchant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ba_email", models.CharField(help_text="Email du BA recruteur (lien avec MySQL brand_ambassadors)", max_length=255)),
                ("nom", models.CharField(max_length=100)),
                ("prenom", models.CharField(max_length=100)),
                ("telephone", models.CharField(max_length=30, unique=True)),
                ("adresse", models.CharField(blank=True, default="", max_length=255)),
                ("numero_merchant", models.CharField(help_text="Numéro marchand Airtel Money", max_length=50, unique=True)),
                ("nom_commerce", models.CharField(max_length=200)),
                ("photo_id_recto", models.TextField(blank=True, default="", help_text="Pièce d'identité - recto (base64)")),
                ("photo_id_verso", models.TextField(blank=True, default="", help_text="Pièce d'identité - verso (base64)")),
                ("photo_rccm", models.TextField(blank=True, default="", help_text="Document de commerce RCCM (base64)")),
                ("statut", models.CharField(choices=[("INSCRIT", "Inscrit"), ("ACTIF", "Actif"), ("SUSPENDU", "Suspendu"), ("REJETÉ", "Rejeté")], default="INSCRIT", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Marchand",
                "verbose_name_plural": "Marchands",
                "ordering": ["-created_at"],
            },
        ),
    ]
