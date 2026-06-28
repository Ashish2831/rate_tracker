# Fresh initial migration — Django owns raw ingest only; dbt owns analytics marts.

import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="RawResponse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("external_id", models.CharField(db_index=True, max_length=64, unique=True)),
                ("source_url", models.URLField(max_length=512)),
                ("raw_body", models.JSONField()),
                ("fetched_at", models.DateTimeField(db_index=True)),
                (
                    "parse_status",
                    models.CharField(
                        choices=[
                            ("success", "Success"),
                            ("failed", "Failed"),
                            ("partial", "Partial"),
                        ],
                        default="success",
                        max_length=16,
                    ),
                ),
                ("error_message", models.TextField(blank=True, default="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "indexes": [
                    models.Index(fields=["fetched_at"], name="rates_rawre_fetched_b5a8f5_idx"),
                    models.Index(fields=["created_at"], name="rates_rawre_created_8b7c87_idx"),
                ],
            },
        ),
    ]
