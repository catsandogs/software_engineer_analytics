from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.index, name='index'),
    path('general-stats/', views.general_stats, name='general_stats'),
    path('demand/', views.demand, name='demand'),
    path('geography/', views.geography, name='geography'),
    path('skills/', views.skills, name='skills'),
    path('latest-vacancies/', views.latest_vacancies, name='latest_vacancies'),
    path('api/chart-data/<str:chart_type>/', views.chart_data_api, name='chart_data_api'),
]