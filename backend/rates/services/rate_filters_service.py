"""Filter metadata service — provider and rate-type options for dashboard dropdowns."""

from rates.repositories.rate_repository import RateRepository


class RateFiltersService:
    """SRP — read filter options from the database."""

    def __init__(self, repository: RateRepository | None = None):
        self.repository = repository or RateRepository()

    def get_options(self) -> dict[str, list[str]]:
        providers, rate_types = self.repository.get_filter_options()
        return {"providers": providers, "rate_types": rate_types}
