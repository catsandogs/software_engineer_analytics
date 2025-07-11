import plotly
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from .models import PageContent, StatisticalData, SiteConfiguration, VacancyData
import requests
import logging
import json
from django.core.serializers.json import DjangoJSONEncoder

from datetime import datetime, timedelta
import plotly.graph_objs as go
import json
from django.utils.safestring import mark_safe
from django.utils.safestring import mark_safe
import json
import plotly.graph_objects as go
from plotly.offline import plot

logger = logging.getLogger(__name__)


def get_site_config():
    """Get site configuration, create default if doesn't exist"""
    config, created = SiteConfiguration.objects.get_or_create(
        pk=1,
        defaults={
            'site_title': 'Software Engineer Analytics Hub',
            'site_description': 'Comprehensive analytics for Software Engineer profession',
            'footer_text': 'Студент: Тренихин Михаил Александрович | Группа: РИ-231003 | Курс: Технологии программирования'
        }
    )
    return config


def get_page_content(page_name):
    """Get page content or create default"""
    try:
        return PageContent.objects.get(page=page_name, is_active=True)
    except PageContent.DoesNotExist:
        return None


def index(request):
    """Main page with Software Engineer profession description"""
    config = get_site_config()
    page_content = get_page_content('main')

    if not page_content:
        # Create default content for main page
        page_content = PageContent.objects.create(
            page='main',
            title='Инженер-программист',
            description='Комплексная аналитика и статистика по профессии инженер-программист',
            content_html="""
            <div class="profession-description">
                <h3>О профессии Инженер-программист</h3>
                <p>Инженер-программист — это специалист, который занимается разработкой, проектированием и сопровождением программного обеспечения. Эта профессия находится на пересечении инженерных наук и информационных технологий, требуя глубоких знаний как в области программирования, так и в системном анализе.</p>

                <h4>Основные обязанности и навыки</h4>
                <p>Инженеры-программисты отвечают за весь жизненный цикл программного продукта: от анализа требований и проектирования архитектуры до разработки, тестирования и внедрения. Они должны владеть множественными языками программирования, понимать принципы объектно-ориентированного программирования, работать с базами данных и системами контроля версий.</p>

                <h4>Области применения</h4>
                <p>Профессия инженера-программиста востребована в различных отраслях: от разработки веб-приложений и мобильных приложений до создания систем управления предприятием, игр, и программного обеспечения для научных исследований. Специалисты работают в IT-компаниях, банках, телекоммуникационных компаниях, государственных учреждениях.</p>

                <h4>Карьерные перспективы</h4>
                <p>Карьерный рост инженера-программиста может идти по техническому пути (от junior до senior разработчика, архитектора) или по управленческому (team lead, project manager, CTO). Профессия предоставляет отличные возможности для удаленной работы и международных проектов.</p>

                <h4>Компенсация и льготы</h4>
                <p>Инженеры-программисты получают конкурентоспособную заработную плату, которая значительно зависит от уровня навыков, опыта работы и специализации. Многие компании предоставляют дополнительные льготы: медицинское страхование, обучение, гибкий график работы.</p>
            </div>
            """
        )

    context = {
        'config': config,
        'page_content': page_content,
    }
    return render(request, 'analytics/index.html', context)


from django.http import HttpRequest
from unittest.mock import Mock


# def general_stats(request):
#     """General statistics page"""
#     config = get_site_config()
#     page_content = get_page_content('general_stats')
#
#     # Получаем объекты StatisticalData
#     salary_dynamics = StatisticalData.objects.filter(data_type='demand_salary', is_active=True).first()
#     vacancy_count = StatisticalData.objects.filter(data_type='demand_vacancy', is_active=True).first()
#     salary_by_city = StatisticalData.objects.filter(data_type='geo_salary', is_active=True).first()
#     vacancy_by_city = StatisticalData.objects.filter(data_type='geo_vacancy', is_active=True).first()
#     top_skills = StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first()
#
#     # Создаем структуру данных, соответствующую ожиданиям шаблона
#     stats_data = {
#         'salary_dynamics': {
#             'chart_image': salary_dynamics.raw_data if salary_dynamics else salary_dynamics,
#             'table_html': salary_dynamics.raw_data if salary_dynamics else None,
#         },
#         'vacancy_count': {
#             'chart_image': vacancy_count.raw_data if vacancy_count else None,
#             'table_html': vacancy_count.raw_data if vacancy_count else None,
#         },
#         'salary_by_city': {
#             'chart_image': salary_by_city.raw_data if salary_by_city else None,
#             'table_html': salary_by_city.raw_data if salary_by_city else None,
#         },
#         'vacancy_by_city': {
#             'chart_image': vacancy_by_city.raw_data if vacancy_by_city else None,
#             'table_html': vacancy_by_city.raw_data if vacancy_by_city else None,
#         },
#         'top_skills': {
#             'chart_image': top_skills.raw_data if top_skills else top_skills,
#             'table_html': top_skills.raw_data if top_skills else None,
#         },
#     }
#
#     print(top_skills)
#     context = {
#         'config': config,
#         'page_content': page_content,
#         'stats_data': stats_data,
#     }
#     return render(request, 'analytics/general_stats.html', context)
def general_stats(request):
    config = get_site_config()
    page_content = get_page_content('general_stats')

    # Функция для преобразования данных в формат для Chart.js
    def prepare_chart_data(stat_data):
        if not stat_data:
            return None
        # Предполагаем, что raw_data содержит словарь с данными
        return {
            'labels': stat_data.raw_data['labels'],
            'data': stat_data.raw_data['datasets'][0]['data']
        }

    stats_data = {
        'salary_dynamics': prepare_chart_data(
            StatisticalData.objects.filter(data_type='demand_salary', is_active=True).first()
        ),
        'vacancy_count': prepare_chart_data(
            StatisticalData.objects.filter(data_type='demand_vacancy', is_active=True).first()
        ),
        'salary_by_city': prepare_chart_data(
            StatisticalData.objects.filter(data_type='geo_salary', is_active=True).first()
        ),
        'vacancy_by_city': prepare_chart_data(
            StatisticalData.objects.filter(data_type='geo_vacancy', is_active=True).first()
        ),
        'top_skills': (
            {'labels': list(
                StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first().raw_data['skills'][
                    '2003'].keys()),
             'data':
                 StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first().raw_data['skills'][
                     '2003']
             }
        ),

    }
    print({'labels': StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first().raw_data[
        'labels'],
           'data': list(
               StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first().raw_data['skills'][
                   '2003'].keys())
           })
    return render(request, 'analytics/general_stats.html', {
        'config': config,
        'page_content': page_content,
        'stats_data': stats_data
    })


# analytics/views.py

def demand(request):
    config = get_site_config()
    page_content = get_page_content('demand')

    # Ищем данные по всем возможным типам
    salary_data = StatisticalData.objects.filter(
        data_type='demand_salary',  # Только тот тип, который используется в import_vacancies.py
        is_active=True
    ).first()

    vacancy_data = StatisticalData.objects.filter(
        data_type='demand_vacancy',  # Только тот тип, который используется в import_vacancies.py
        is_active=True
    ).first()

    context = {
        'config': config,
        'page_content': page_content,
        'stats_data': {
            'salary_dynamics': salary_data,
            'vacancy_count': vacancy_data,
        }
    }
    return render(request, 'analytics/demand.html', context)


def geography(request):
    print("✅ geography view вызван")

    salary_data = StatisticalData.objects.filter(data_type='geo_salary', is_active=True).first()
    vacancy_data = StatisticalData.objects.filter(data_type='geo_vacancy', is_active=True).first()
    config = get_site_config()
    page_content = get_page_content('geography')
    print("Salary data:", salary_data.raw_data['labels'])
    print("Salary data:", (salary_data.raw_data['datasets'])[0]['data'])
    print("Vacancy data:", vacancy_data.raw_data['labels'])
    print("Vacancy data:", vacancy_data.raw_data['datasets'][0]['data'])
    data_table_city = salary_data.raw_data['labels']
    data_table_val = (salary_data.raw_data['datasets'])[0]['data']
    table_vac = vacancy_data.raw_data['labels']
    table_vac1 = vacancy_data.raw_data['datasets'][0]['data']
    TEST_SALARY_DATA = {
        'cities': data_table_city,
        'salaries': data_table_val,
        'chart_type': 'bar'
    }

    TEST_VACANCY_DATA = {
        'cities': vacancy_data.raw_data['labels'],
        'vacancies': vacancy_data.raw_data['datasets'][0]['data'],
        'chart_type': 'pie'
    }

    context = {
        'config': config,
        'page_content': page_content,
        'stats_data': {
            'salary_by_city': {
                'chart_data': TEST_SALARY_DATA,  # Замените на None для проверки реальных данных
                'table_data': [

                    {'city': data_table_city[i], 'value': data_table_val[i]} for i in range(len(data_table_city))
                ]
            },
            'vacancy_by_city': {
                'chart_data': TEST_VACANCY_DATA,  # Замените на None для проверки реальных данных
                'table_data': [
                    {'city': table_vac[i], 'value': table_vac1[i]} for i in range(len(table_vac))
                ]
            }
        }
    }

    return render(request, 'analytics/geography.html', context)


# stop here

def skills(request):
    """Skills analysis page"""
    config = get_site_config()
    page_content = get_page_content('skills')

    # Получаем данные о навыках с дополнительными проверками
    skills_data = StatisticalData.objects.filter(data_type='skills_by_year', is_active=True).first()

    # Если данных нет, попробуем найти альтернативные варианты
    if not skills_data:
        skills_data = StatisticalData.objects.filter(
            data_type__icontains='skills',  # Ищем любые записи, содержащие 'skills'
            is_active=True
        ).first()

    # Логирование для отладки
    logger.debug(f"Skills data: {skills_data}")
    if skills_data and hasattr(skills_data, 'raw_data'):
        logger.debug(f"Raw skills data: {skills_data.raw_data}")

    # Проверяем наличие файла шаблона
    template_path = 'analytics/skills.html'

    context = {
        'config': config,
        'page_content': page_content,
        'stats_data': {
            'skills_by_year': skills_data,
        },
        'debug_data': skills_data.raw_data if skills_data else None,  # Для отладки в шаблоне
    }

    return render(request, template_path, context)


def latest_vacancies(request):
    """Latest vacancies page - shows from database and optionally from API"""
    config = get_site_config()
    page_content = get_page_content('latest_vacancies')

    # Get latest Software Engineer vacancies from database
    latest_db_vacancies = VacancyData.objects.filter(
        is_software_engineer=True
    ).order_by('-published_at')[:10]

    # Try to get from API if enabled
    api_vacancies = []
    if config.hh_api_enabled:
        try:
            api_vacancies = fetch_hh_vacancies(config)
        except Exception as e:
            logger.error(f"Error fetching API vacancies: {e}")
    print(api_vacancies)
    context = {
        'config': config,
        'page_content': page_content,
        'db_vacancies': latest_db_vacancies,
        'api_vacancies': api_vacancies,
        'api_enabled': config.hh_api_enabled,
    }
    return render(request, 'analytics/latest_vacancies.html', context)


def fetch_hh_vacancies(config):
    """Fetch vacancies from HeadHunter API"""
    keywords = config.profession_keywords.split(',')
    search_text = ' OR '.join([kw.strip() for kw in keywords])

    yesterday = datetime.now() - timedelta(days=1)
    date_from = yesterday.strftime('%Y-%m-%d')

    params = {
        'text': search_text,
        'area': 1,  # Moscow
        'date_from': date_from,
        'per_page': config.max_api_requests,
        'order_by': 'publication_time',
        'search_field': 'name'
    }

    response = requests.get('https://api.hh.ru/vacancies', params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    vacancies = []

    for item in data.get('items', []):
        vacancy = {
            'id': item['id'],
            'name': item['name'],
            'employer': item.get('employer', {}).get('name', 'Unknown'),
            'area': item.get('area', {}).get('name', 'Unknown'),
            'salary': format_salary(item.get('salary')),
            'published_at': format_date(item.get('published_at')),
            'url': item.get('alternate_url', '#'),
            'skills': 'Детали на сайте hh.ru',
            'description': 'Полное описание доступно на сайте hh.ru'
        }
        vacancies.append(vacancy)
    print(data)
    return vacancies


def format_salary(salary_data):
    """Format salary information"""
    if not salary_data:
        return 'Не указана'

    from_amount = salary_data.get('from')
    to_amount = salary_data.get('to')
    currency = salary_data.get('currency', 'RUB')

    if from_amount and to_amount:
        return f"{from_amount:,} - {to_amount:,} {currency}"
    elif from_amount:
        return f"от {from_amount:,} {currency}"
    elif to_amount:
        return f"до {to_amount:,} {currency}"
    else:
        return 'Не указана'


def format_date(date_string):
    """Format publication date"""
    if not date_string:
        return 'Дата не указана'

    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime('%d.%m.%Y %H:%M')
    except Exception:
        return date_string


# API endpoints for chart data
def chart_data_api(request, chart_type):
    """API endpoint for chart data"""
    try:
        stat_data = StatisticalData.objects.filter(data_type=chart_type, is_active=True).first()

        if stat_data and stat_data.raw_data:
            return JsonResponse(stat_data.raw_data)
        else:
            return JsonResponse({
                'error': f'No data available for {chart_type}',
                'labels': [],
                'data': []
            })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)