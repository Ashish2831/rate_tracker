"""Management command: ingest rates from a live HTTP JSON endpoint."""

from django.core.management.base import BaseCommand, CommandError

from rates.services.ingestion import IngestionService


class Command(BaseCommand):
    help = "Ingest rates from a live HTTP JSON endpoint (uses scraper + parser)."

    def add_arguments(self, parser):
        parser.add_argument("url", type=str, help="HTTP(S) URL returning a rate JSON payload")

    def handle(self, *args, **options):
        url = options["url"]
        self.stdout.write(f"Ingesting rates from {url}...")
        service = IngestionService()
        try:
            stats = service.ingest_from_path(url)
        except Exception as exc:
            raise CommandError(f"HTTP ingest failed: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("HTTP ingest complete."))
        for key, value in stats.items():
            self.stdout.write(f"  {key}: {value}")
