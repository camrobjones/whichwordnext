# Generated by Django 4.1.7 on 2024-03-09 20:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nwp', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Skip',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('guesses', models.IntegerField()),
                ('passageToken', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nwp.passagetoken')),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='nwp.profile')),
            ],
        ),
    ]
