from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="escrow",
            name="confirmation_code",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
