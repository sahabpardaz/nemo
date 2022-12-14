# Generated by Django 2.2.27 on 2022-04-13 04:59
# and then manually modified: The 'django_prometheus.models.Mixin' inheritance notation got removed from the relevant operations.
#
# Motive of modification:
# There is a class named 'Mixin' that is dynamically created by django-prometheus. Some models in Nemo have used it.
# The mixin overrides some methods to trace model CRUDs and hence has no effect on the model's schema. But, Django
# denotes the Mixin inheritance in the auto-generated CreateModel migrations and since the mixins are dynamically-created
# the resulting migrations encounter an AttributeError: module 'django_prometheus.models' has no attribute 'Mixin'.
# Unfortunately, there isn't a standard way to handle such a case, currently.
# For more details see: https://github.com/korfuri/django-prometheus/issues/42

import apps.devops_metrics.models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_prometheus.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('dashboard', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChangeList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=500, null=True)),
                ('commit_hash', models.CharField(max_length=40, validators=[apps.devops_metrics.models.validate_commit_hash])),
                ('time', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('change_list_id', models.CharField(max_length=100)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.Project')),
            ],
            options={
                'ordering': ('-time',),
            },
        ),
        migrations.CreateModel(
            name='ServiceStatusReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('U', 'up'), ('D', 'down')], max_length=1)),
                ('time', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.Environment')),
            ],
            options={
                'ordering': ('-time',),
            },
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('P', 'pass'), ('F', 'fail')], max_length=1)),
                ('time', models.DateTimeField(blank=True, default=django.utils.timezone.now)),
                ('change_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='devops_metrics.ChangeList')),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='dashboard.Environment')),
            ],
            options={
                'ordering': ('-time',),
            },
        ),
        migrations.AddConstraint(
            model_name='changelist',
            constraint=models.UniqueConstraint(fields=('project', 'change_list_id'), name='unique_change_list_id_in_project'),
        ),
        migrations.AddConstraint(
            model_name='changelist',
            constraint=models.UniqueConstraint(fields=('project', 'commit_hash'), name='unique_commit_hash_in_project'),
        ),
    ]
