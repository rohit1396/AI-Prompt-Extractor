# Generated manually for Cloudinary-backed image storage.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_extraction_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extraction',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='extractions/%Y/%m/%d/'),
        ),
        migrations.AddField(
            model_name='extraction',
            name='cloudinary_public_id',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='extraction',
            name='cloudinary_secure_url',
            field=models.URLField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='extraction',
            name='cloudinary_version',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='extraction',
            name='storage_provider',
            field=models.CharField(
                choices=[('local', 'Local'), ('cloudinary', 'Cloudinary')],
                default='local',
                max_length=20,
            ),
        ),
    ]
