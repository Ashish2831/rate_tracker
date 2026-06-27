"""Django admin registrations for debugging and data inspection."""

from django.contrib import admin
from django.utils import timezone

from rates.models import Provider, Rate, RawResponse


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "normalized_name", "created_at")
    search_fields = ("name", "normalized_name")


@admin.register(RawResponse)
class RawResponseAdmin(admin.ModelAdmin):
    list_display = ("external_id", "source_url", "parse_status", "fetched_at")
    list_filter = ("parse_status",)
    search_fields = ("external_id", "source_url")
    date_hierarchy = "fetched_at"


class IngestedLast24HoursFilter(admin.SimpleListFilter):
    """Schema.md query pattern #3 — rates ingested in the last 24 hours."""

    title = "ingestion window"
    parameter_name = "last_24h"

    def lookups(self, request, model_admin):
        return (("yes", "Last 24 hours"),)

    def queryset(self, request, queryset):
        if self.value() == "yes":
            cutoff = timezone.now() - timezone.timedelta(hours=24)
            return queryset.filter(ingestion_ts__gte=cutoff)
        return queryset


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ("provider", "rate_type", "rate_value", "effective_date", "ingestion_ts")
    list_filter = ("rate_type", "currency", IngestedLast24HoursFilter, "raw_response__parse_status")
    search_fields = ("provider__name", "rate_type")
    date_hierarchy = "ingestion_ts"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("provider", "raw_response")

    @admin.display(description="Parse status", ordering="raw_response__parse_status")
    def parse_status_via_raw(self, obj):
        if obj.raw_response_id:
            return obj.raw_response.parse_status
        return "—"
