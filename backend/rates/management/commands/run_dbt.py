"""Management command: run dbt models to refresh analytics marts."""

from django.core.management.base import BaseCommand, CommandError

from rates.services.dbt_runner import DbtRunError, DbtRunner


class Command(BaseCommand):
    help = "Run dbt models (staging → marts) against the current Postgres database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full-refresh",
            action="store_true",
            help="Rebuild all incremental models from scratch",
        )

    def handle(self, *args, **options):
        runner = DbtRunner()
        try:
            output = runner.run_marts(full_refresh=options["full_refresh"])
        except DbtRunError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("dbt run complete."))
        if output.strip():
            self.stdout.write(output[-2000:])
