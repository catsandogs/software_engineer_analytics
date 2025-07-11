
from django.db import models


class AnalyticsDataupload(models.Model):
    file_name = models.CharField(max_length=500)
    file_size = models.BigIntegerField()
    upload_date = models.DateTimeField()
    processed_records = models.IntegerField()
    software_engineer_records = models.IntegerField()
    processing_notes = models.TextField()
    is_processed = models.BooleanField()

    class Meta:
        managed = False
        db_table = 'analytics_dataupload'


class AnalyticsPagecontent(models.Model):
    page = models.CharField(unique=True, max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    content_html = models.TextField()
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'analytics_pagecontent'


class AnalyticsSiteconfiguration(models.Model):
    site_title = models.CharField(max_length=200)
    site_description = models.TextField()
    footer_text = models.TextField()
    profession_keywords = models.TextField()
    hh_api_enabled = models.BooleanField()
    max_api_requests = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'analytics_siteconfiguration'


class AnalyticsStatisticaldata(models.Model):
    data_type = models.CharField(unique=True, max_length=50)
    title = models.CharField(max_length=200)
    description = models.TextField()
    chart_image = models.CharField(max_length=100)
    table_html = models.TextField()
    raw_data = models.JSONField(blank=True, null=True)
    is_active = models.BooleanField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'analytics_statisticaldata'


class AnalyticsVacancydata(models.Model):
    vacancy_id = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=500)
    description = models.TextField()
    key_skills = models.TextField()
    experience = models.CharField(max_length=100)
    employment = models.CharField(max_length=100)
    schedule = models.CharField(max_length=100)
    salary_from = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    salary_to = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float
    salary_currency = models.CharField(max_length=10)
    salary_gross = models.BooleanField(blank=True, null=True)
    employer_name = models.CharField(max_length=300)
    area_name = models.CharField(max_length=200)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField()
    is_software_engineer = models.BooleanField()
    salary_in_rub = models.DecimalField(max_digits=10, decimal_places=5, blank=True, null=True)  # max_digits and decimal_places have been guessed, as this database handles decimal fields as float

    class Meta:
        managed = False
        db_table = 'analytics_vacancydata'


class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'
