"""Run dbt models after raw ingest to refresh analytics marts."""

import logging
import os
import subprocess

from django.conf import settings

logger = logging.getLogger("rates.dbt")


class DbtRunError(RuntimeError):
    """Raised when dbt run exits with a non-zero status."""


class DbtRunner:
    """Shell out to dbt CLI — transforms raw responses into analytics marts."""

    def __init__(self, project_dir: str | None = None, profiles_dir: str | None = None):
        self.project_dir = str(project_dir or settings.DBT_PROJECT_DIR)
        self.profiles_dir = str(profiles_dir or settings.DBT_PROFILES_DIR)

    def run_marts(self, full_refresh: bool = False) -> str:
        """Build staging → intermediate → mart models (incremental by default)."""
        args = ["run"]
        if full_refresh:
            args.append("--full-refresh")
        return self._run(args)

    def _run(self, args: list[str]) -> str:
        cmd = [
            "dbt",
            *args,
            "--project-dir",
            self.project_dir,
            "--profiles-dir",
            self.profiles_dir,
        ]
        logger.info(
            "Starting dbt",
            extra={"event": "dbt_start", "command": " ".join(cmd)},
        )
        env = os.environ.copy()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            logger.error(
                "dbt failed",
                extra={
                    "event": "dbt_error",
                    "returncode": result.returncode,
                    "stderr": result.stderr[-4000:],
                },
            )
            raise DbtRunError(result.stderr or result.stdout or "dbt run failed")

        logger.info(
            "dbt completed",
            extra={"event": "dbt_end", "stdout_tail": result.stdout[-500:]},
        )
        return result.stdout
