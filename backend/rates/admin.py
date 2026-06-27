"""Django admin — raw bronze layer and dbt mart inspection (read-only)."""

from django.contrib import admin

from rates.models import MartLatestRate, MartRate, RawResponse


@admin.register(RawResponse)
class RawResponseAdmin(admin.ModelAdmin):
    """Inspect immutable scrape payloads and parse outcomes."""

    list_display = ("external_id", "source_url", "parse_status", "fetched_at", "created_at")
    list_filter = ("parse_status",)
    search_fields = ("external_id", "source_url")
    date_hierarchy = "fetched_at"


@admin.register(MartRate)
class MartRateAdmin(admin.ModelAdmin):
    """dbt mart_rates — read-only inspection of transformed facts."""

    list_display = ("provider_name", "rate_type", "rate_value", "effective_date", "ingestion_ts")
    list_filter = ("rate_type", "currency")
    search_fields = ("provider_name", "rate_type", "external_id")
    date_hierarchy = "ingestion_ts"
    list_per_page = 50
    show_full_result_count = False

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MartLatestRate)
class MartLatestRateAdmin(admin.ModelAdmin):
    """dbt mart_latest_rates — read-only latest snapshot per provider/type."""

    list_display = ("provider_name", "rate_type", "rate_value", "effective_date", "ingestion_ts")
    list_filter = ("rate_type",)
    search_fields = ("provider_name", "rate_type")
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
