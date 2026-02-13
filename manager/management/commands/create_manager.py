"""
Crée un utilisateur manager Django.
Usage: python manage.py create_manager --email admin@taxiconnect.cg --password MonMotDePasse --name "Nkounkou Alain"
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from manager.models import ManagerProfile


class Command(BaseCommand):
    help = "Crée un compte manager pour le dashboard"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--password", required=True)
        parser.add_argument("--name", default="Manager")

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"]
        name_parts = options["name"].split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user, created = User.objects.get_or_create(
            username=email,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": True,
            }
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f"✅ Utilisateur créé: {email}"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Utilisateur existe déjà: {email}"))

        profile, p_created = ManagerProfile.objects.get_or_create(
            user=user, defaults={"role": "manager"}
        )
        if p_created:
            self.stdout.write(self.style.SUCCESS(f"✅ Profil manager créé"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️ Profil manager existe déjà"))

        self.stdout.write(self.style.SUCCESS(f"\n🔗 Connexion: /manager/"))
        self.stdout.write(self.style.SUCCESS(f"   Email: {email}"))
        self.stdout.write(self.style.SUCCESS(f"   Mot de passe: {password}"))
