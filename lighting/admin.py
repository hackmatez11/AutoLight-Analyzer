from django.contrib import admin
from .models import LightingCatalog, CADFile, Room, Fixture, Report


@admin.register(LightingCatalog)
class LightingCatalogAdmin(admin.ModelAdmin):
    list_display = ['symbol_name', 'brand', 'model_number', 'lumens', 'wattage', 'unit_cost']
    list_filter = ['brand']
    search_fields = ['symbol_name', 'brand', 'model_number']
    ordering = ['symbol_name']


@admin.register(CADFile)
class CADFileAdmin(admin.ModelAdmin):
    list_display = ['project_name', 'user', 'filename', 'status', 'uploaded_at']
    list_filter = ['status', 'uploaded_at']
    search_fields = ['project_name', 'filename', 'user__username']
    readonly_fields = ['uploaded_at', 'processed_at']
    ordering = ['-uploaded_at']


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'cad_file', 'area', 'height', 'required_lux', 'current_lux']
    list_filter = ['cad_file']
    search_fields = ['name', 'cad_file__project_name']
    ordering = ['cad_file', 'name']


@admin.register(Fixture)
class FixtureAdmin(admin.ModelAdmin):
    list_display = ['lighting_catalog', 'room', 'quantity', 'total_cost']
    list_filter = ['lighting_catalog', 'room__cad_file']
    search_fields = ['lighting_catalog__symbol_name', 'room__name']
    ordering = ['room', 'lighting_catalog']


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ['cad_file', 'report_type', 'generated_at']
    list_filter = ['report_type', 'generated_at']
    search_fields = ['cad_file__project_name']
    readonly_fields = ['generated_at']
    ordering = ['-generated_at']
