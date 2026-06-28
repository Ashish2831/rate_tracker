"""Management command: run dbt models to refresh analytics marts."""

from django.core.management.base import BaseCommand, CommandError

from rates.services.dbt_runner import DbtRunError, DbtRunner
from rates.services.mart_bootstrap import marts_exist


class Command(BaseCommand):
    help = "Run dbt models (staging → marts) against the current Postgres database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--full-refresh",
            action="store_true",
            help="Rebuild all incremental models from scratch",
        )
        parser.add_argument(
            "--if-missing",
            action="store_true",
            help="Skip unless analytics.mart_latest_rates does not exist yet",
        )

    def handle(self, *args, **options):
        full_refresh = options["full_refresh"] or not marts_exist()

        if options["if_missing"] and marts_exist():
            self.stdout.write("Analytics marts already exist — skipping dbt run.")
            return

        runner = DbtRunner()
        try:
            output = runner.run_marts(full_refresh=full_refresh)
        except DbtRunError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("dbt run complete."))
        if output.strip():
            self.stdout.write(output[-2000:])
