from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_extraction_cloudinary_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='extraction',
            name='raw_ocr_text',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='extraction',
            name='classification_label',
            field=models.CharField(
                blank=True,
                choices=[('prompt', 'Prompt'), ('not_prompt', 'Not prompt'), ('uncertain', 'Uncertain')],
                default='',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='extraction',
            name='classification_score',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='extraction',
            name='classification_confidence',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='extraction',
            name='matched_signals',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name='extraction',
            name='classifier_version',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
    ]
