# Unmanaged ORM mirrors for dbt-built tables — state only, no Django DDL.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rates", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="MartRate",
            fields=[
                ("id", models.BigIntegerField(primary_key=True, serialize=False)),
                ("provider_name", models.CharField(max_length=128)),
                ("normalized_name", models.CharField(db_index=True, max_length=128)),
                ("rate_type", models.CharField(db_index=True, max_length=64)),
                ("rate_value", models.DecimalField(decimal_places=4, max_digits=8)),
                ("effective_date", models.DateField(db_index=True)),
                ("ingestion_ts", models.DateTimeField(db_index=True)),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("external_id", models.CharField(max_length=64, unique=True)),
            ],
            options={
                "db_table": '"analytics"."mart_rates"',
                "ordering": ["-effective_date", "-ingestion_ts"],
                "managed": False,
            },
        ),
        migrations.CreateModel(
            name="MartLatestRate",
            fields=[
                ("id", models.BigIntegerField(primary_key=True, serialize=False)),
                ("provider_name", models.CharField(max_length=128)),
                ("normalized_name", models.CharField(db_index=True, max_length=128)),
                ("rate_type", models.CharField(db_index=True, max_length=64)),
                ("rate_value", models.DecimalField(decimal_places=4, max_digits=8)),
                ("effective_date", models.DateField()),
                ("ingestion_ts", models.DateTimeField()),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("external_id", models.CharField(max_length=64, unique=True)),
            ],
            options={
                "db_table": '"analytics"."mart_latest_rates"',
                "ordering": ["provider_name", "rate_type"],
                "managed": False,
            },
        ),
    ]
