import csv
import os
import json
import decimal  # Добавляем импорт decimal
from decimal import Decimal, InvalidOperation  # Импортируем нужные классы
from django.core.management.base import BaseCommand
from analytics.models import StatisticalData, DataUpload, VacancyData
from datetime import datetime
import traceback  # Для детального вывода ошибок
import os
import csv
import json
import decimal
import hashlib
import traceback
from collections import defaultdict  # Добавляем этот импорт
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal, InvalidOperation
from analytics.models import VacancyData, StatisticalData, DataUpload

class Command(BaseCommand):
    help = 'Import profession analytics data from vacancies CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def parse_date(self, date_str):
        """Парсим дату из различных форматов"""
        formats = [
            '%Y-%m-%dT%H:%M:%S%z',  # 2023-01-15T12:34:56+0300
            '%Y-%m-%d',  # 2023-01-15
            '%d.%m.%Y',  # 15.01.2023
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def safe_decimal(self, value):
        """Безопасное преобразование в Decimal"""
        try:
            return Decimal(value) if value.strip() else None
        except (decimal.InvalidOperation, ValueError, AttributeError):
            return None

    def calculate_avg_salary(self, salary_from, salary_to, currency):
        """Рассчитываем среднюю зарплату с конвертацией в рубли"""
        if not salary_from and not salary_to:
            return None

        try:
            salary_from = self.safe_decimal(salary_from) if salary_from else None
            salary_to = self.safe_decimal(salary_to) if salary_to else None

            if salary_from is None and salary_to is None:
                return None

            avg = (salary_from + salary_to) / 2 if salary_from and salary_to else (salary_from or salary_to)

            # Конвертация в рубли
            rates = {
                'USD': 75,
                'EUR': 80,
                'KZT': 0.2,
                'UAH': 2,
                'BYR': 25
            }
            return avg * rates.get(currency, 1)  # Если валюта не указана, считаем что это рубли
        except Exception as e:
            self.stdout.write(f"Error calculating avg salary: {e}")
            return None

    def parse_skills(self, row):
        """Улучшенный парсинг навыков из строки CSV"""
        if 'key_skills' not in row:
            return []

        skills_str = row['key_skills'].strip()
        if not skills_str:
            return []

        # Попробуем разные варианты форматов
        try:
            # Вариант 1: JSON-массив
            skills = json.loads(skills_str)
            if isinstance(skills, list):
                return [str(skill).strip() for skill in skills]
        except json.JSONDecodeError:
            pass

        # Вариант 2: Разделители
        delimiters = ['\n', '|', ';', ',', '/']
        for delim in delimiters:
            if delim in skills_str:
                return [s.strip() for s in skills_str.split(delim) if s.strip()]

        # Вариант 3: Одиночный навык
        return [skills_str] if skills_str else []

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        # Проверка существования файла
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'Файл не найден: {csv_file_path}'))
            return

        # Создаем запись о загрузке
        upload = DataUpload.objects.create(
            file_name=os.path.basename(csv_file_path),
            file_size=os.path.getsize(csv_file_path)
        )

        processed_count = 0
        error_count = 0
        batch_size = 1000  # Размер батча для bulk_create
        vacancies_batch = []

        # Структуры для агрегированных данных
        stats = {
            'salary': defaultdict(list),
            'vacancies': defaultdict(int),
            'skills': defaultdict(lambda: defaultdict(int)),
            'geo_salaries': defaultdict(list),
            'geo_vacancies': defaultdict(int)
        }

        self.stdout.write(f'Начинаем импорт из {csv_file_path}...')

        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)

                # Проверка обязательных колонок
                required_columns = {'name', 'salary_from', 'salary_to',
                                    'salary_currency', 'area_name', 'published_at'}
                if missing := required_columns - set(reader.fieldnames):
                    self.stdout.write(self.style.ERROR(
                        f'Отсутствуют обязательные колонки: {missing}'))
                    return

                for row_num, row in enumerate(reader, 1):
                    try:
                        # Парсинг базовых данных
                        title = row['name'].strip()
                        published_at = self.parse_date(row['published_at'].strip())
                        if not title or not published_at:
                            continue

                        # Обработка зарплаты
                        salary_from = self.safe_decimal(row['salary_from'])
                        salary_to = self.safe_decimal(row['salary_to'])
                        currency = row['salary_currency'].strip()
                        avg_salary = self.calculate_avg_salary(salary_from, salary_to, currency)

                        # Обработка местоположения
                        city = row['area_name'].strip()

                        # Парсинг навыков
                        skills = self.parse_skills(row)

                        # Генерация уникального ID если нужно
                        vacancy_id = hashlib.md5(
                            json.dumps(row, sort_keys=True).encode()
                        ).hexdigest()

                        # Подготовка объекта вакансии
                        vacancy = VacancyData(
                            vacancy_id=vacancy_id,
                            name=title,
                            salary_from=salary_from,
                            salary_to=salary_to,
                            salary_currency=currency,
                            area_name=city,
                            published_at=published_at,
                            key_skills=", ".join(skills) if skills else None,
                            salary_in_rub=avg_salary,
                            # Дополнительные поля...
                        )
                        vacancies_batch.append(vacancy)

                        # Агрегация статистики
                        year = str(published_at.year)
                        if avg_salary:
                            stats['salary'][year].append(avg_salary)
                            if city:
                                stats['geo_salaries'][city].append(avg_salary)

                        stats['vacancies'][year] += 1
                        if city:
                            stats['geo_vacancies'][city] += 1

                        for skill in skills:
                            stats['skills'][year][skill] += 1

                        processed_count += 1
                        print(processed_count)

                        # Пакетное сохранение
                        if len(vacancies_batch) >= batch_size:
                            self._bulk_save_vacancies(vacancies_batch)
                            vacancies_batch = []
                        if processed_count == 110_000:
                            break
                    except Exception as e:
                        error_count += 1
                        self._log_error(row_num, row, e)
                        continue

                # Сохраняем оставшиеся вакансии
                if vacancies_batch:
                    self._bulk_save_vacancies(vacancies_batch)

                # Сохранение статистики
                self._save_statistics(stats)

                # Финализация загрузки
                upload.processed_records = processed_count
                upload.error_count = error_count
                upload.is_processed = True
                upload.processing_notes = (
                    f'Обработано вакансий: {processed_count}\n'
                    f'Ошибок: {error_count}\n'
                    f'Последняя дата: {published_at}'
                )
                upload.save()

                self.stdout.write(self.style.SUCCESS(
                    f'Импорт завершен! Успешно: {processed_count}, Ошибок: {error_count}'
                ))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Критическая ошибка: {str(e)}'))
            upload.is_processed = False
            upload.processing_notes = f'Ошибка: {str(e)}'
            upload.save()
            return

    def _bulk_save_vacancies(self, vacancies):
        """Пакетное сохранение вакансий с обработкой дубликатов"""
        try:
            VacancyData.objects.bulk_create(
                vacancies,
                update_conflicts=True,
                update_fields=[
                    'name', 'salary_from', 'salary_to',
                    'salary_currency', 'area_name',
                    'key_skills', 'salary_in_rub'
                ],
                unique_fields=['vacancy_id']
            )
        except Exception as e:
            self.stdout.write(f"Ошибка пакетного сохранения: {str(e)}")
            # Альтернатива: сохраняем по одной
            for vacancy in vacancies:
                try:
                    vacancy.save()
                except Exception as e:
                    self.stdout.write(f"Ошибка сохранения вакансии: {str(e)}")

    def _log_error(self, row_num, row, error):
        """Логирование ошибок с деталями"""
        self.stdout.write(f"\n⚠️ Ошибка в строке {row_num}:")
        self.stdout.write(f"Тип: {type(error).__name__}")
        self.stdout.write(f"Сообщение: {str(error)}")

        # Для ошибок Decimal выводим проблемные значения
        if isinstance(error, (decimal.InvalidOperation, decimal.ConversionSyntax)):
            self.stdout.write("Проблемные значения зарплаты:")
            self.stdout.write(f"salary_from: {row.get('salary_from')}")
            self.stdout.write(f"salary_to: {row.get('salary_to')}")

        # Сокращенный вывод строки для логов
        sample_data = {k: v for k, v in row.items() if k in [
            'name', 'salary_from', 'salary_to', 'area_name', 'published_at'
        ]}
        self.stdout.write(f"Данные строки: {sample_data}")

    def _save_statistics(self, stats):
        """Сохранение агрегированной статистики"""
        # Сохранение данных по годам
        StatisticalData.objects.update_or_create(
            data_type='salary_by_year',
            defaults=self._prepare_chart_data(
                stats['salary'],
                'Динамика зарплат по годам',
                'Средняя зарплата (руб)'
            )
        )

        StatisticalData.objects.update_or_create(
            data_type='vacancies_by_year',
            defaults=self._prepare_chart_data(
                stats['vacancies'],
                'Динамика вакансий по годам',
                'Количество вакансий'
            )
        )


    def _prepare_chart_data(self, data, title, label):
        """Подготовка данных для графиков"""
        sorted_years = sorted(data.keys())
        return {
            'title': title,
            'raw_data': {
                'labels': sorted_years,
                'datasets': [{
                    'label': label,
                    'data': [data[y] if isinstance(data[y], (int, float))
                             else sum(data[y]) / len(data[y]) for y in sorted_years]
                }]
            },
            'is_active': True
        }
    def save_statistical_data(self, salary_data, vacancy_data, skills_data, geo_data):
        """Сохраняем агрегированные статистические данные"""
        # Сохраняем данные по зарплатам
        if salary_data:
            years = sorted(salary_data.keys())
            avg_salaries = [sum(salary_data[y]) / len(salary_data[y]) for y in years]

            StatisticalData.objects.update_or_create(
                data_type='demand_salary',
                defaults={
                    'title': 'Динамика зарплат по годам',
                    'raw_data': {
                        'labels': years,
                        'datasets': [{
                            'label': 'Средняя зарплата (руб)',
                            'data': avg_salaries
                        }]
                    },
                    'is_active': True
                }
            )

        # Сохраняем данные по вакансиям
        if vacancy_data:
            years = sorted(vacancy_data.keys())
            counts = [vacancy_data[y] for y in years]

            StatisticalData.objects.update_or_create(
                data_type='demand_vacancy',
                defaults={
                    'title': 'Динамика количества вакансий по годам',
                    'raw_data': {
                        'labels': years,
                        'datasets': [{
                            'label': 'Количество вакансий',
                            'data': counts
                        }]
                    },
                    'is_active': True
                }
            )

        # Сохраняем данные по навыкам
        if skills_data:
            all_skills = {}
            for year, skills in skills_data.items():
                for skill, count in skills.items():
                    all_skills[skill] = all_skills.get(skill, 0) + count

            top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:20]

            StatisticalData.objects.update_or_create(
                data_type='skills_by_year',
                defaults={
                    'title': 'Топ навыков по годам',
                    'raw_data': {
                        'labels': list(skills_data.keys()),
                        'skills': {k: dict(v) for k, v in skills_data.items()},
                        'top_skills': [skill[0] for skill in top_skills],
                        'top_skills_data': [skill[1] for skill in top_skills],
                    },
                    'is_active': True
                }
            )

        # Сохраняем географические данные
        if geo_data['salaries'] and geo_data['vacancies']:
            # Топ-10 городов по зарплатам
            city_salaries = {city: sum(sals) / len(sals) for city, sals in geo_data['salaries'].items() if sals}
            top_salary_cities = dict(sorted(city_salaries.items(), key=lambda x: x[1], reverse=True)[:10])

            # Топ-10 городов по вакансиям
            top_vacancy_cities = dict(sorted(geo_data['vacancies'].items(),
                                             key=lambda x: x[1], reverse=True)[:10])

            StatisticalData.objects.update_or_create(
                data_type='geo_salary',
                defaults={
                    'title': 'Уровень зарплат по городам',
                    'raw_data': {
                        'labels': list(top_salary_cities.keys()),
                        'datasets': [{
                            'label': 'Средняя зарплата (руб)',
                            'data': list(top_salary_cities.values())
                        }]
                    },
                    'is_active': True
                }
            )

            StatisticalData.objects.update_or_create(
                data_type='geo_vacancy',
                defaults={
                    'title': 'Доля вакансий по городам',
                    'raw_data': {
                        'labels': list(top_vacancy_cities.keys()),
                        'datasets': [{
                            'label': 'Количество вакансий',
                            'data': list(top_vacancy_cities.values())
                        }]
                    },
                    'is_active': True
                }
            )