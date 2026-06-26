from django.contrib import admin

from .models import Provider, Rate, RawResponse


@admin.register(Provider)
class ProviderAdmin(admin.ModelAdmin):
    list_display = ("name", "normalized_name", "created_at")
    search_fields = ("name", "normalized_name")


@admin.register(RawResponse)
class RawResponseAdmin(admin.ModelAdmin):
    list_display = ("external_id", "source_url", "parse_status", "fetched_at")
    list_filter = ("parse_status",)
    search_fields = ("external_id", "source_url")


@admin.register(Rate)
class RateAdmin(admin.ModelAdmin):
    list_display = ("provider", "rate_type", "rate_value", "effective_date", "ingestion_ts")
    list_filter = ("rate_type", "currency")
    search_fields = ("provider__name", "rate_type")
