from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import PageContent, StatisticalData, VacancyData, SiteConfiguration, DataUpload

@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    list_display = ['page', 'title', 'is_active', 'updated_at']
    list_filter = ['page', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Page Information', {
            'fields': ('page', 'title', 'description', 'is_active')
        }),
        ('Content', {
            'fields': ('content_html',),
            'classes': ('wide',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['page']
        return self.readonly_fields

@admin.register(StatisticalData)
class StatisticalDataAdmin(admin.ModelAdmin):
    list_display = ['data_type', 'title', 'has_chart', 'has_table', 'is_active', 'updated_at']
    list_filter = ['data_type', 'is_active', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_at', 'updated_at', 'chart_preview']
    
    fieldsets = (
        ('Data Information', {
            'fields': ('data_type', 'title', 'description', 'is_active')
        }),
        ('Chart Data', {
            'fields': ('chart_image', 'chart_preview'),
            'classes': ('wide',)
        }),
        ('Table Data', {
            'fields': ('table_html',),
            'classes': ('wide',)
        }),
        ('Raw Data (JSON)', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_chart(self, obj):
        return bool(obj.chart_image)
    has_chart.boolean = True
    has_chart.short_description = 'Chart'
    
    def has_table(self, obj):
        return bool(obj.table_html)
    has_table.boolean = True
    has_table.short_description = 'Table'
    
    def chart_preview(self, obj):
        if obj.chart_image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px;" />',
                obj.chart_image.url
            )
        return "No chart uploaded"
    chart_preview.short_description = 'Chart Preview'
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['data_type']
        return self.readonly_fields

@admin.register(VacancyData)
class VacancyDataAdmin(admin.ModelAdmin):
    list_display = ['name', 'employer_name', 'area_name', 'salary_display', 'is_software_engineer', 'published_at']
    list_filter = ['is_software_engineer', 'salary_currency', 'area_name', 'published_at']
    search_fields = ['name', 'employer_name', 'area_name', 'key_skills']
    readonly_fields = ['vacancy_id', 'created_at']
    list_editable = ['is_software_engineer']
    date_hierarchy = 'published_at'
    
    fieldsets = (
        ('Vacancy Information', {
            'fields': ('vacancy_id', 'name', 'employer_name', 'area_name', 'is_software_engineer')
        }),
        ('Job Details', {
            'fields': ('description', 'key_skills', 'experience', 'employment', 'schedule'),
            'classes': ('collapse',)
        }),
        ('Salary Information', {
            'fields': ('salary_from', 'salary_to', 'salary_currency', 'salary_gross', 'salary_in_rub')
        }),
        ('Dates', {
            'fields': ('published_at', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def salary_display(self, obj):
        if obj.salary_from or obj.salary_to:
            salary_parts = []
            if obj.salary_from:
                salary_parts.append(f"от {obj.salary_from:,.0f}")
            if obj.salary_to:
                salary_parts.append(f"до {obj.salary_to:,.0f}")
            return f"{' '.join(salary_parts)} {obj.salary_currency}"
        return "Не указана"
    salary_display.short_description = 'Salary'
    
    actions = ['mark_as_software_engineer', 'mark_as_not_software_engineer']
    
    def mark_as_software_engineer(self, request, queryset):
        updated = queryset.update(is_software_engineer=True)
        self.message_user(request, f'{updated} vacancies marked as Software Engineer positions.')
    mark_as_software_engineer.short_description = "Mark selected as Software Engineer"
    
    def mark_as_not_software_engineer(self, request, queryset):
        updated = queryset.update(is_software_engineer=False)
        self.message_user(request, f'{updated} vacancies marked as NOT Software Engineer positions.')
    mark_as_not_software_engineer.short_description = "Mark selected as NOT Software Engineer"

@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Site Information', {
            'fields': ('site_title', 'site_description', 'footer_text')
        }),
        ('Profession Settings', {
            'fields': ('profession_keywords',),
            'description': 'Keywords used to identify Software Engineer positions from vacancy data'
        }),
        ('API Settings', {
            'fields': ('hh_api_enabled', 'max_api_requests'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one configuration
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the configuration
        return False

@admin.register(DataUpload)
class DataUploadAdmin(admin.ModelAdmin):
    list_display = ['file_name', 'file_size_mb', 'upload_date', 'processed_records', 'software_engineer_records', 'is_processed']
    list_filter = ['is_processed', 'upload_date']
    search_fields = ['file_name', 'processing_notes']
    readonly_fields = ['upload_date', 'file_size_mb']
    
    fieldsets = (
        ('File Information', {
            'fields': ('file_name', 'file_size_mb', 'upload_date')
        }),
        ('Processing Results', {
            'fields': ('processed_records', 'software_engineer_records', 'is_processed', 'processing_notes')
        }),
    )
    
    def file_size_mb(self, obj):
        return f"{obj.file_size / (1024 * 1024):.2f} MB"
    file_size_mb.short_description = 'File Size'
    
    def has_add_permission(self, request):
        # Data uploads are typically created programmatically
        return False

# Customize admin site headers
admin.site.site_header = "Software Engineer Analytics Admin"
admin.site.site_title = "Analytics Admin"
admin.site.index_title = "Analytics Management"