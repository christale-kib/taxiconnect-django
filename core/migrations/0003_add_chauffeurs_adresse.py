from django.db import migrations, connection
def forwards(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM chauffeurs LIKE 'adresse';")
        if cursor.fetchone() is None:
            cursor.execute("ALTER TABLE chauffeurs ADD COLUMN adresse VARCHAR(255) NULL;")
def backwards(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("SHOW COLUMNS FROM chauffeurs LIKE 'adresse';")
        if cursor.fetchone() is not None:
            cursor.execute("ALTER TABLE chauffeurs DROP COLUMN adresse;")
class Migration(migrations.Migration):
    dependencies = [
        ("core", "0002_brandambassadors_challenges_chauffeurs_commissions_and_more"),
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]