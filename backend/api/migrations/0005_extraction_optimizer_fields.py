from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_extraction_classification_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='extraction',
            name='optimized_prompt',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='extraction',
            name='optimizer_template',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
        migrations.AddField(
            model_name='extraction',
            name='optimizer_components',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name='extraction',
            name='optimizer_version',
            field=models.CharField(blank=True, default='', max_length=30),
        ),
    ]
