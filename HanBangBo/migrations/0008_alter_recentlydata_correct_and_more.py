# Generated by Django 5.1.6 on 2025-03-01 07:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('HanBangBo', '0007_userchoice_source_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recentlydata',
            name='correct',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='recentlydata',
            name='type_value',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='userchoice',
            name='type_value',
            field=models.CharField(max_length=255),
        ),
    ]
