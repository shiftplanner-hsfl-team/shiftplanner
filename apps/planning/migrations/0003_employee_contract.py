import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('planning', '0002_month_deadline'),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='contract_type',
            field=models.CharField(
                choices=[
                    ('vollzeit', 'Vollzeit'),
                    ('teilzeit', 'Teilzeit'),
                    ('studierende', 'Studierende'),
                    ('minijob', 'Minijob'),
                ],
                default='teilzeit',
                max_length=20,
                verbose_name='Vertragsart',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='employee',
            name='weekly_hours',
            field=models.DecimalField(
                decimal_places=1,
                max_digits=4,
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(48),
                ],
                verbose_name='Wochenstunden',
            ),
        ),
    ]
