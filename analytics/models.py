from django.db import models
from django.core.validators import FileExtensionValidator

class PageContent(models.Model):
    """Model for managing page content through Django admin"""
    
    PAGE_CHOICES = [
        ('main', 'Main Page'),
        ('general_stats', 'General Statistics'),
        ('demand', 'Demand Analysis'),
        ('geography', 'Geography Analysis'),
        ('skills', 'Skills Analysis'),
        ('latest_vacancies', 'Latest Vacancies'),
    ]
    
    page = models.CharField(max_length=50, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    content_html = models.TextField(
        help_text="HTML content for the page body",
        blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"
    
    def __str__(self):
        return f"{self.get_page_display()} - {self.title}"

class StatisticalData(models.Model):
    """Model for storing statistical data and charts"""
    
    DATA_TYPES = [
        ('salary_dynamics', 'Salary Dynamics by Year'),
        ('vacancy_count', 'Vacancy Count by Year'),
        ('salary_by_city', 'Salary by City'),
        ('vacancy_by_city', 'Vacancy by City'),
        ('top_skills', 'Top Skills'),
        ('demand_salary', 'Software Engineer Salary Dynamics'),
        ('demand_vacancy', 'Software Engineer Vacancy Count'),
        ('geo_salary', 'Geographic Salary Analysis'),
        ('geo_vacancy', 'Geographic Vacancy Analysis'),
        ('skills_by_year', 'Skills by Year Analysis'),
    ]
    
    data_type = models.CharField(max_length=50, choices=DATA_TYPES, unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    
    # Chart as image file
    chart_image = models.ImageField(
        upload_to='charts/',
        validators=[FileExtensionValidator(allowed_extensions=['png', 'jpg', 'jpeg', 'svg'])],
        help_text="Upload chart as PNG, JPG, or SVG file"
    )
    chart_image = models.ImageField(upload_to='charts/', null=True, blank=True)
    # Table data as HTML
    table_html = models.TextField(
        help_text="HTML table with statistical data",
        blank=True
    )
    
    # Raw data for API endpoints (JSON format)
    raw_data = models.JSONField(
        help_text="Raw data in JSON format for charts",
        blank=True,
        null=True
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Statistical Data"
        verbose_name_plural = "Statistical Data"
    
    def __str__(self):
        return f"{self.get_data_type_display()}"

class VacancyData(models.Model):
    """Model for storing processed vacancy data from CSV"""
    
    vacancy_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=500)
    description = models.TextField(blank=True)
    key_skills = models.TextField(blank=True)
    experience = models.CharField(max_length=100, blank=True)
    employment = models.CharField(max_length=100, blank=True)
    schedule = models.CharField(max_length=100, blank=True)
    
    # Salary information
    salary_from = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_to = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(max_length=10, blank=True)
    salary_gross = models.BooleanField(null=True, blank=True)
    
    # Company and location
    employer_name = models.CharField(max_length=300, blank=True)
    area_name = models.CharField(max_length=200, blank=True)
    
    # Dates
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Processing flags
    is_software_engineer = models.BooleanField(default=False, help_text="Is this a Software Engineer position?")
    salary_in_rub = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Salary converted to RUB")
    
    class Meta:
        verbose_name = "Vacancy Data"
        verbose_name_plural = "Vacancy Data"
        ordering = ['-published_at']
    
    def __str__(self):
        return f"{self.name} - {self.employer_name}"

class SiteConfiguration(models.Model):
    """Model for site-wide configuration"""
    
    site_title = models.CharField(max_length=200, default="Software Engineer Analytics Hub")
    site_description = models.TextField(default="Comprehensive analytics for Software Engineer profession")
    footer_text = models.TextField(
        default="Студент: Иванов Иван Иванович | Группа: ИВТ-21-1 | Курс: Анализ данных и визуализация"
    )
    profession_keywords = models.TextField(
        default="инженер, инженер-программист, инженер, ИТ-инженер, инженер-разработчик",
        help_text="Keywords for identifying Software Engineer positions (comma-separated)"
    )
    
    # API settings
    hh_api_enabled = models.BooleanField(default=False)
    max_api_requests = models.IntegerField(default=10)
    
    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"
    
    def __str__(self):
        return self.site_title
    
    def save(self, *args, **kwargs):
        # Ensure only one configuration exists
        if not self.pk and SiteConfiguration.objects.exists():
            raise ValueError("Only one site configuration is allowed")
        super().save(*args, **kwargs)

class DataUpload(models.Model):
    """Model for tracking CSV data uploads"""
    
    file_name = models.CharField(max_length=500)
    file_size = models.BigIntegerField(help_text="File size in bytes")
    upload_date = models.DateTimeField(auto_now_add=True)
    processed_records = models.IntegerField(default=0)
    software_engineer_records = models.IntegerField(default=0)
    processing_notes = models.TextField(blank=True)
    is_processed = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Data Upload"
        verbose_name_plural = "Data Uploads"
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.file_name} - {self.upload_date.strftime('%Y-%m-%d %H:%M')}"