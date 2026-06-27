"""Management command: bulk-load rates from the assessment seed parquet file."""

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from rates.services.ingestion import IngestionService


class Command(BaseCommand):
    help = "Load rate data from the seed parquet file into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default=settings.SEED_PARQUET_PATH,
            help="Path to the parquet seed file",
        )

    def handle(self, *args, **options):
        path = options["path"]
        self.stdout.write(f"Seeding rates from {path}...")
        service = IngestionService()
        try:
            stats = service.ingest_from_parquet(path)
        except FileNotFoundError as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:
            raise CommandError(f"Seed failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("Seed complete."))
        for key, value in stats.items():
            self.stdout.write(f"  {key}: {value}")
