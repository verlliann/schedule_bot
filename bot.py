from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import sqlite3
import asyncio

API_TOKEN = 'YOUR_TOKEN'

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()  # Хранилище состояний в памяти
dp = Dispatcher(storage=storage)

# Словарь соответствия групп и баз данных
GROUPS = {
    'Р22К2': 'r22k2.db',
    'Р22Б1': 'r22b1.db',
    'Р22Б2': 'r22b2.db',
    'Р22О': 'r22o.db',
    'Р22И': 'r22i.db',
    'Р22Оин': 'r22oin.db',
    'Р22Т': 'r22t.db',
    'Р22К1': 'r22k1.db',
}

# Определяем состояния для FSM
class ScheduleStates(StatesGroup):
    waiting_for_date = State()  # Ожидание ввода даты


# Функция для подключения к базе данных и получения расписания
def get_schedule_for_date_and_group(date, group):
    db_path = GROUPS.get(group)
    if not db_path:
        return f"Группа {group} не найдена."

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT groups, time, discipline, lesson_type, location, teacher 
        FROM schedule 
        WHERE date = ?
    ''', (date,))

    rows = cursor.fetchall()
    conn.close()
    if rows:
        schedule = f"Расписание на {date} для группы {group}:\n" + '-' * 50 + '\n'
        for row in rows:
            groups, time, discipline, lesson_type, location, teacher = row
            schedule += (f"Группы: {groups}\n"
                         f"Время: {time}\n"
                         f"Дисциплина: {discipline}\n"
                         f"Тип занятия: {lesson_type}\n"
                         f"Место: {location}\n"
                         f"Преподаватель: {teacher}\n\n")
        return schedule
    else:
        return f"Расписание на {date} для группы {group} не найдено."


# Команда для показа меню выбора группы
@dp.message(Command('start'))
async def start_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=group, callback_data=f"group_{group}")] for group in GROUPS.keys()
    ])
    await message.answer("Выберите группу:", reply_markup=keyboard)


# Обработчик выбора группы
@dp.callback_query(lambda callback: callback.data.startswith('group_'))
async def select_group(callback: CallbackQuery):
    group = callback.data.split('_')[1]
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Сегодня", callback_data=f"date_{group}_today"),
                InlineKeyboardButton(text="Завтра", callback_data=f"date_{group}_tomorrow")
            ],
            [
                InlineKeyboardButton(text="Выбрать дату", callback_data=f"custom_date_{group}")
            ]
        ]
    )
    await callback.message.edit_text(f"Группа {group} выбрана. Выберите день:", reply_markup=keyboard)


# Обработчик выбора даты
@dp.callback_query(lambda callback: callback.data.startswith('date_'))
async def select_date(callback: CallbackQuery):
    _, group, day = callback.data.split('_')
    if day == 'today':
        date = datetime.now().strftime('%d.%m.%Y')
    elif day == 'tomorrow':
        date = (datetime.now() + timedelta(days=1)).strftime('%d.%m.%Y')
    elif day == 'day_after_tomorrow':
        date = (datetime.now() + timedelta(days=2)).strftime('%d.%m.%Y')
    else:
        await callback.answer("Некорректный выбор.", show_alert=True)
        return

    schedule = get_schedule_for_date_and_group(date, group)
    await callback.message.edit_text(schedule)


# Обработчик кнопки "Выбрать дату"
@dp.callback_query(lambda callback: callback.data.startswith('custom_date_'))
async def custom_date(callback: CallbackQuery, state: FSMContext):
    group = callback.data.split('_')[2]
    await state.set_state(ScheduleStates.waiting_for_date)
    await state.update_data(group=group)  # Сохраняем группу в состояние
    await callback.message.edit_text("Введите дату в формате 'dd.mm.yyyy':")


# Обработчик ввода произвольной даты
@dp.message(ScheduleStates.waiting_for_date)
async def process_custom_date(message: Message, state: FSMContext):
    user_data = await state.get_data()
    group = user_data.get("group")

    try:
        date = datetime.strptime(message.text, '%d.%m.%Y').strftime('%d.%m.%Y')
        schedule = get_schedule_for_date_and_group(date, group)
        await message.answer(schedule)
    except ValueError:
        await message.answer("Некорректный формат даты. Попробуйте ещё раз.")
        return

    await state.clear()  # Сбрасываем состояние


# Запуск бота
async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
