from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_projectreview'),
    ]

    operations = [
        migrations.AddField(
            model_name='escrow',
            name='client_approved_release_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='escrow',
            name='manual_release_requested_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='escrow',
            name='manual_release_synced_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='escrow',
            name='client_release_comment',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='escrow',
            name='client_release_experience',
            field=models.CharField(blank=True, max_length=20),
        ),
    ]
