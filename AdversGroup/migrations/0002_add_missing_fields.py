from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('AdversGroup', '0001_initial'),  # Убедитесь, что имя приложения правильное
    ]

    operations = [
        # Добавляем отсутствующие поля
        migrations.AddField(
            model_name='shopperdesign',
            name='printing_method',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('silk', 'Шелкография'),
                    ('embroidery', 'Вышивка'),
                    ('transfer', 'Полноцвет с трансфером')
                ],
                default='silk',
            ),
        ),
        migrations.AddField(
            model_name='shopperdesign',
            name='printing_side',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('front', 'Лицевая сторона'),
                    ('back', 'Обратная сторона'),
                    ('both', 'Обе стороны')
                ],
                default='front',
            ),
        ),
        migrations.AddField(
            model_name='shopperdesign',
            name='canvas_width',
            field=models.FloatField(null=True, blank=True, help_text="Ширина холста в мм"),
        ),
        migrations.AddField(
            model_name='shopperdesign',
            name='canvas_height',
            field=models.FloatField(null=True, blank=True, help_text="Высота холста в мм"),
        ),

        migrations.AlterField(
            model_name='shopperdesign',
            name='final_pdf',
            field=models.FileField(upload_to='designs/pdf/', null=True, blank=True),
        ),
    ]