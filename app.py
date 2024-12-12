import sqlite3
from bs4 import BeautifulSoup
from collections import defaultdict
import os

# Функция для обработки одного HTML-файла
def process_html_file(file_path, db_name):
    # Читаем HTML
    with open(file_path, 'r', encoding='utf-8') as file:
        html = file.read()

    # Парсинг HTML с помощью BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr', class_='table-active')

    # Подключение к базе данных
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Создание таблицы, если её нет
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            groups TEXT,
            date TEXT,
            time TEXT,
            discipline TEXT,
            lesson_type TEXT,
            location TEXT,
            teacher TEXT,
            weekday TEXT,
            lesson_time TEXT,
            UNIQUE(groups, date, time)
        )
    ''')

    # Обработка строк расписания
    for row in rows:
        lesson_date = row.get('data-date')
        lesson_time = row.get('data-lesson-time')
        weekday = row.get('data-weekday')

        groups = row.find('td', class_='text-center').get_text(strip=True)
        time_info = row.find('td', class_='time-column').get_text(strip=True)
        discipline = row.find('td', class_='discipline-column').get_text(strip=True)
        lesson_type = row.find_all('td', class_='text-center')[1].get_text(strip=True)
        location = row.find_all('td', class_='text-center')[2].get_text(strip=True)
        teacher = row.find('td', class_='staff-column').get_text(strip=True)

        # Проверка на существование записи
        cursor.execute('''
            SELECT * FROM schedule 
            WHERE groups = ? AND date = ? AND time = ?
        ''', (groups, lesson_date, time_info))

        result = cursor.fetchone()

        if result is None:
            cursor.execute('''
                INSERT INTO schedule (groups, date, time, discipline, lesson_type, location, teacher, weekday, lesson_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (groups, lesson_date, time_info, discipline, lesson_type, location, teacher, weekday, lesson_time))
            print(f"Добавлено: {groups}, {lesson_date}, {time_info}")
        else:
            print(f"Запись уже существует: {groups}, {lesson_date}, {time_info}")

    conn.commit()
    conn.close()

# Основной блок для обработки папки
def process_folder(folder_path):
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.html'):
            file_path = os.path.join(folder_path, file_name)
            db_name = f"{os.path.splitext(file_name)[0]}.db"
            print(f"Обработка файла: {file_name}")
            process_html_file(file_path, db_name)

# Укажи путь к папке с файлами
folder_path = 'html'
process_folder(folder_path)
