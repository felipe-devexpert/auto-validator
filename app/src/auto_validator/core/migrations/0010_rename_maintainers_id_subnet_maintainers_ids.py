# Generated by Django 4.2.16 on 2024-09-18 20:50

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_rename_mainnet_netid_subnet_mainnet_id_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="subnet",
            old_name="maintainers_id",
            new_name="maintainers_ids",
        ),
    ]
