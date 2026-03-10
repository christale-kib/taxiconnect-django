from django.contrib.auth.models import User

users = [
    # (username, email, password, is_superuser, is_staff)
    ("admin@taxiconnect.cg",    "admin@taxiconnect.cg",    "admin123",         True,  True),
    ("ba@taxiconnect.cg",       "ba@taxiconnect.cg",       "Ba001@cg",         False, False),
    ("taxi@taxiconnect.cg",     "taxi@taxiconnect.cg",     "Taxi001@cg",       False, False),
    ("manager@taxiconnect.cg",  "manager@taxiconnect.cg",  "Manager001@cg",    False, False),
    ("merchant@taxiconnect.cg", "merchant@taxiconnect.cg", "Merchant001@cg",   False, False),
]

for username, email, password, is_superuser, is_staff in users:
    if User.objects.filter(username=username).exists():
        u = User.objects.get(username=username)
        u.set_password(password)
        u.is_superuser = is_superuser
        u.is_staff = is_staff
        u.save()
        print(f"[UPDATED] {username}")
    else:
        User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_superuser=is_superuser,
            is_staff=is_staff,
        )
        print(f"[CREATED] {username}")

print("\n✅ Tous les utilisateurs sont prêts.")
print("\n--- RÉCAPITULATIF ---")
print(f"{'Page':<25} {'URL':<35} {'Email':<30} {'Mot de passe'}")
print("-" * 120)
print(f"{'BA App':<25} {'/':<35} {'ba@taxiconnect.cg':<30} Ba001@cg")
print(f"{'Taxi App':<25} {'/taxi/':<35} {'taxi@taxiconnect.cg':<30} Taxi001@cg")
print(f"{'Manager Dashboard':<25} {'/manager/':<35} {'manager@taxiconnect.cg':<30} Manager001@cg")
print(f"{'Merchant App':<25} {'/merchant/':<35} {'merchant@taxiconnect.cg':<30} Merchant001@cg")
print(f"{'Merchant Dashboard':<25} {'/merchant/dashboard/':<35} {'merchant@taxiconnect.cg':<30} Merchant001@cg")
print(f"{'Django Admin':<25} {'/admin/':<35} {'admin@taxiconnect.cg':<30} admin123")
