from django.db import migrations, models
import django.contrib.auth.models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='image_url',
            field=models.TextField(blank=True, verbose_name='Link ảnh thiết bị (hoặc tải ảnh từ máy)'),
        ),
        migrations.CreateModel(
            name='CustomerAccount',
            fields=[],
            options={
                'verbose_name': 'Tài khoản người dùng',
                'verbose_name_plural': 'Tài khoản người dùng',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('auth.user',),
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
