# Generated by Django 5.1.6 on 2025-02-27 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HanBangBo', '0003_alter_recentlydata_keyword_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=255)),
                ('assigned_value', models.IntegerField()),
            ],
        ),
    ]
