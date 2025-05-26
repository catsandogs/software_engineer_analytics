import csv
import os
import json
from django.core.management.base import BaseCommand
from analytics.models import StatisticalData, DataUpload
from datetime import datetime
from decimal import Decimal


class Command(BaseCommand):
    help = 'Import profession analytics data from vacancies CSV file'

    def save_geo_data(self, geo_data):
        """Сохраняем данные по городам в StatisticalData"""
        if not geo_data['salaries'] or not geo_data['vacancies']:
            return

        # Подготовка данных по зарплатам
        city_salaries = {city: sum(sals) / len(sals) for city, sals in geo_data['salaries'].items() if sals}
        sorted_salaries = dict(sorted(city_salaries.items(), key=lambda x: x[1], reverse=True)[:10])

        # Подготовка данных по вакансиям
        city_vacancies = geo_data['vacancies']
        sorted_vacancies = dict(sorted(city_vacancies.items(), key=lambda x: x[1], reverse=True)[:10])

        # Сохраняем данные по зарплатам по городам
        StatisticalData.objects.update_or_create(
            data_type='geo_salary',
            defaults={
                'title': 'Уровень зарплат по городам',
                'raw_data': {
                    'labels': list(sorted_salaries.keys()),
                    'datasets': [{
                        'label': 'Средняя зарплата (руб)',
                        'data': list(sorted_salaries.values())
                    }]
                },
                'is_active': True
            }
        )

        # Сохраняем данные по вакансиям по городам
        StatisticalData.objects.update_or_create(
            data_type='geo_vacancy',
            defaults={
                'title': 'Доля вакансий по городам',
                'raw_data': {
                    'labels': list(sorted_vacancies.keys()),
                    'datasets': [{
                        'label': 'Количество вакансий',
                        'data': list(sorted_vacancies.values())
                    }]
                },
                'is_active': True
            }
        )
    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to CSV file')

    def aggregate_geo_data(self, geo_data, city, avg_salary):
        """Агрегируем данные по городам"""
        if not city:
            return

        if city not in geo_data['salaries']:
            geo_data['salaries'][city] = []
        if avg_salary:
            geo_data['salaries'][city].append(avg_salary)
        geo_data['vacancies'][city] = geo_data['vacancies'].get(city, 0) + 1
    def handle(self, *args, **options):
        csv_file_path = options['csv_file']
        geo_salary_data = {}
        geo_vacancy_data = {}
        if not os.path.exists(csv_file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_file_path}'))
            return

        # Create upload record
        file_size = os.path.getsize(csv_file_path)
        upload = DataUpload.objects.create(
            file_name=os.path.basename(csv_file_path),
            file_size=file_size
        )

        processed_count = 0
        error_count = 0
        salary_data = {}
        vacancy_data = {}
        skills_data = {}
        geo_data = {
            'salaries': {},
            'vacancies': {}
        }
        self.stdout.write(f'Starting import of {csv_file_path}...')

        try:
            with open(csv_file_path, 'r', encoding='utf-8-sig') as file:  # Изменено на utf-8-sig
                # Читаем первые 5 строк для отладки
                sample_lines = [next(file) for _ in range(5)]
                self.stdout.write("Sample CSV lines:")
                for line in sample_lines:
                    self.stdout.write(line.strip())

                file.seek(0)  # Возвращаемся к началу файла
                reader = csv.DictReader(file)

                required_columns = ['name', 'salary_from', 'salary_to', 'salary_currency',
                                    'area_name', 'published_at']
                if not all(col in reader.fieldnames for col in required_columns):
                    missing = set(required_columns) - set(reader.fieldnames)
                    self.stdout.write(self.style.ERROR(
                        f'Missing required columns: {missing}'
                    ))
                    return

                self.stdout.write(f"CSV columns: {reader.fieldnames}")  # Отладочный вывод

                for row_num, row in enumerate(reader, 1):
                    try:
                        # Извлекаем данные из строки CSV
                        title = row['name'].strip()
                        salary_from = Decimal(row['salary_from']) if row['salary_from'].strip() else None
                        salary_to = Decimal(row['salary_to']) if row['salary_to'].strip() else None
                        currency = row['salary_currency'].strip()
                        city = row['area_name'].strip()
                        published_at = self.parse_date(row['published_at'].strip())
                        avg_salary = self.calculate_avg_salary(salary_from, salary_to, currency)
                        # Улучшенный парсинг навыков
                        skills = self.parse_skills(row)
                        if row_num <= 5:  # Выводим навыки из первых 5 строк для отладки
                            self.stdout.write(f"Row {row_num} raw skills: {row.get('key_skills', 'N/A')}")
                            self.stdout.write(f"Row {row_num} parsed skills: {skills}")

                        if not title or not published_at:
                            continue

                        # Получаем год из даты публикации
                        year = str(published_at.year)

                        # Рассчитываем среднюю зарплату
                        avg_salary = self.calculate_avg_salary(salary_from, salary_to, currency)

                        # Агрегируем данные для статистики
                        self.aggregate_salary_data(salary_data, year, avg_salary)
                        self.aggregate_vacancy_data(vacancy_data, year)
                        self.aggregate_geo_data(geo_data, city, avg_salary)
                        if skills:
                            self.aggregate_skills_data(skills_data, year, skills)
                        elif row_num <= 10:  # Логируем первые 10 строк без навыков
                            self.stdout.write(f"Row {row_num}: No skills found in: {row.get('key_skills', 'N/A')}")

                        processed_count += 1
                        city = row['area_name'].strip()
                        if city:
                            if avg_salary:
                                if city not in geo_salary_data:
                                    geo_salary_data[city] = []
                                geo_salary_data[city].append(avg_salary)

                            # Для подсчета вакансий по городам
                            geo_vacancy_data[city] = geo_vacancy_data.get(city, 0) + 1
                        if processed_count == 100000:
                            self.stdout.write(f'Processed {processed_count} records...')
                            break

                    except Exception as e:
                        error_count += 1
                        self.stdout.write(f'Error processing row {row_num}: {e}')
                        continue

            # Сохраняем агрегированные данные в StatisticalData
            self.save_salary_data(salary_data)
            self.save_vacancy_data(vacancy_data)
            self.save_skills_data(skills_data)
            self.save_geo_data(geo_data)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading CSV file: {e}'))
            return

        # Обновляем запись о загрузке
        upload.processed_records = processed_count
        upload.is_processed = True
        upload.processing_notes = (
            f'Processed {processed_count} vacancies\n'
            f'Aggregated data for {len(salary_data)} years\n'
            f'Errors: {error_count}'

        )
        print(StatisticalData.objects.filter(data_type='geo_salary'))
        print(StatisticalData.objects.filter(data_type='geo_vacancy', is_active=True))
        upload.save()

        self.stdout.write(
            self.style.SUCCESS(
                f'\nImport completed!\n'
                f'Total processed: {processed_count} vacancies\n'
                f'Years aggregated: {len(salary_data)}\n'
                f'Errors: {error_count}'
            )
        )

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

    def calculate_avg_salary(self, salary_from, salary_to, currency):
        """Рассчитываем среднюю зарплату с конвертацией в рубли"""
        if not salary_from and not salary_to:
            return None

        avg = float(salary_from + salary_to) / 2 if salary_from and salary_to else float(salary_from or salary_to)

        if currency == 'USD':
            return avg * 75
        elif currency == 'EUR':
            return avg * 80
        return avg

    def aggregate_salary_data(self, salary_data, year, avg_salary):
        """Агрегируем данные по зарплатам"""
        if not avg_salary:
            return

        if year not in salary_data:
            salary_data[year] = []
        salary_data[year].append(avg_salary)

    def aggregate_vacancy_data(self, vacancy_data, year):
        """Агрегируем данные по количеству вакансий"""
        if year not in vacancy_data:
            vacancy_data[year] = 0
        vacancy_data[year] += 1

    def aggregate_skills_data(self, skills_data, year, skills):
        """Агрегируем данные по навыкам с отладкой"""
        if not skills:
            if len(skills_data) < 3:  # Логируем только первые несколько раз
                self.stdout.write(f"No skills for year {year}")
            return

        if year not in skills_data:
            skills_data[year] = {}
            self.stdout.write(f"New year added: {year}")

        for skill in skills:
            clean_skill = skill.strip('"\'').strip()  # Очищаем навык
            if clean_skill:
                skills_data[year][clean_skill] = skills_data[year].get(clean_skill, 0) + 1
                if len(skills_data[year]) < 3:  # Логируем первые несколько навыков
                    self.stdout.write(f"Added skill: {clean_skill} to year {year}")

    def save_salary_data(self, salary_data):
        """Сохраняем данные по зарплатам в StatisticalData"""
        if not salary_data:
            return

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

    def save_vacancy_data(self, vacancy_data):
        """Сохраняем данные по вакансиям в StatisticalData"""
        if not vacancy_data:
            return

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

    def save_skills_data(self, skills_data):
        """Сохраняем данные по навыкам в StatisticalData с детальной отладкой"""
        if not skills_data:
            self.stdout.write(self.style.ERROR("No skills data collected!"))
            return

        # Детальный отладочный вывод структуры данных
        self.stdout.write("\nSkills data summary:")
        for year, year_skills in skills_data.items():
            self.stdout.write(f"Year {year}: {len(year_skills)} skills")
            if year_skills:
                top_3 = sorted(year_skills.items(), key=lambda x: x[1], reverse=True)[:3]
                self.stdout.write(f"  Top 3: {top_3}")

        # Собираем все навыки за все годы
        all_skills = {}
        for year_data in skills_data.values():
            for skill, count in year_data.items():
                all_skills[skill] = all_skills.get(skill, 0) + count

        if not all_skills:
            self.stdout.write(self.style.ERROR("No skills found in any year!"))
            return

        # Получаем топ-20 навыков
        top_skills = sorted(all_skills.items(), key=lambda x: x[1], reverse=True)[:20]
        self.stdout.write("\nTop 20 skills across all years:")
        for i, (skill, count) in enumerate(top_skills, 1):
            self.stdout.write(f"{i}. {skill}: {count} mentions")

        # Сохраняем данные
        StatisticalData.objects.update_or_create(
            data_type='skills_by_year',
            defaults={
                'title': 'Топ навыков по годам',
                'raw_data': {
                    'labels': list(skills_data.keys()),
                    'skills': {k: dict(v) for k, v in skills_data.items()},
                    'top_skills': [skill[0] for skill in top_skills],
                    'top_skills_data': [skill[1] for skill in top_skills],
                    'total_skills': sum(len(y) for y in skills_data.values()),
                    'total_mentions': sum(sum(y.values()) for y in skills_data.values())
                },
                'is_active': True
            }
        )


