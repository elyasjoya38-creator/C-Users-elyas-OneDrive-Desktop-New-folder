from django.contrib import admin
from .models import pdc_detials
@admin.register(pdc_detials)
class PdcDetailsAdmin(admin.ModelAdmin):
    list_display = ("title", "producer", "types", "startdate", "enddate", "location")
    list_filter = ("types", "startdate")
    search_fields = ("title", "producer", "location")
