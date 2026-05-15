from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_escrow_confirmation_code'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='qualification_summary',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='portfolio_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='proposal',
            name='relevant_experience',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='proposal',
            name='verification_breakdown',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='proposal',
            name='verification_score',
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='proposal',
            name='verification_status',
            field=models.CharField(
                choices=[
                    ('verified', 'Verified'),
                    ('needs_review', 'Needs Review'),
                    ('rejected', 'Rejected'),
                ],
                default='needs_review',
                max_length=20,
            ),
        ),
    ]
