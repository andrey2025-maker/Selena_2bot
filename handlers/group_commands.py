"""
group_commands.py - Команды для работы в группах и ЛС
!число работает везде, НО НЕ ПЕРЕХВАТЫВАЕТ /start
"""

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import re
import logging
from datetime import datetime

router = Router()
logger = logging.getLogger(__name__)

# ========== МУТАЦИИ И ИХ ПРОЦЕНТЫ ==========
MUTATIONS = {
    "⚪️": {
        "name": "Обычная",
        "percentages": [100, 200, 300, 400],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🟡": {
        "name": "Золотая", 
        "percentages": [50, 75, 100, 125],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "💎": {
        "name": "Алмазная",
        "percentages": [40, 60, 80, 100],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "⚡️": {
        "name": "Электрическая",
        "percentages": [25, 37.5, 50, 62.5],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🔥": {
        "name": "Огненная",
        "percentages": [20, 30, 40, 50],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🦖": {
        "name": "Юрская",
        "percentages": [16.67, 25, 33.33, 41.67],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "❄️": {
        "name": "Снежная",
        "percentages": [16.67, 25, 33.33, 41.67],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🎃": {
        "name": "Хэллуин",
        "percentages": [15.38, 23.08, 30.78, 38.46],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🦃": {
        "name": "Благодарения",
        "percentages": [14.81, 22.22, 29.63, 37.04],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🎄": {
        "name": "Рождество",
        "percentages": [13.33, 20, 26.67, 33.33],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    },
    "🌸🩷": {
        "name": "День святого Валентина",
        "percentages": [12.49, 18.75, 25, 31.24],
        "names": ["Буря", "Аврора", "Вулкан", "Админ"]
    }    
}

# ========== ЭМОДЗИ ДЛЯ РЕЗУЛЬТАТОВ ==========
WEATHER_EMOJIS = {
    "Буря": "💨",
    "Аврора": "🌀",
    "Вулкан": "🌋",
    "Админ": "🪯"
}

# Хранилище для отслеживания авторов сообщений
message_authors = {}

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_mutation_keyboard(number: int) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру для выбора мутации"""
    keyboard = []
    row = []
    
    for i, (emoji, data) in enumerate(MUTATIONS.items(), 1):
        row.append(
            InlineKeyboardButton(
                text=f"{emoji} {data['name']}",
                callback_data=f"mut_{emoji}_{number}"
            )
        )
        
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_weather_keyboard(number: int, mutation_emoji: str) -> InlineKeyboardMarkup:
    """Создает инлайн-клавиатуру для выбора погоды (БЕЗ процентов)"""
    keyboard = []
    row = []
    
    mutation = MUTATIONS[mutation_emoji]
    
    for i, weather_name in enumerate(mutation["names"]):
        emoji = WEATHER_EMOJIS[weather_name]
        
        row.append(
            InlineKeyboardButton(
                text=f"{emoji} {weather_name}",
                callback_data=f"weather_{weather_name}_{mutation_emoji}_{number}"
            )
        )
        
        if (i + 1) % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def check_author(callback: types.CallbackQuery) -> bool:
    """Проверяет, является ли пользователь автором сообщения"""
    message_id = callback.message.message_id
    chat_id = callback.message.chat.id
    key = f"{chat_id}_{message_id}"
    
    author_id = message_authors.get(key)
    if not author_id:
        return True
    
    if callback.from_user.id != author_id:
        await callback.answer("❌ Это не ваш калькулятор!", show_alert=True)
        return False
    
    return True

# ========== ОСНОВНЫЕ КОМАНДЫ - ТОЛЬКО !ЧИСЛО ==========

@router.message(F.text.startswith('!'))  # ВАЖНО: ТОЛЬКО сообщения начинающиеся с '!'
async def handle_exclamation_command(message: Message):
    """Обработка команд с !"""
    text = message.text.strip()
    logger.info(f"🔧 Обработка команды с ! в чате '{message.chat.type}': '{text}'")
    
    match = re.match(r'^!(\d+)$', text)
    if not match:
        logger.warning(f"❌ Неправильный формат команды: {text}")
        return
    
    number = int(match.group(1))
    logger.info(f"✅ Формат правильный! Число: {number}")
    
    keyboard = get_mutation_keyboard(number)
    
    try:
        sent_message = await message.reply(
            f"🧮 <b>Калькулятор мутаций</b>\n\n"
            f"<b>Число:</b> {number}\n"
            f"<b>Выберите мутацию:</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        # Сохраняем автора сообщения
        key = f"{sent_message.chat.id}_{sent_message.message_id}"
        message_authors[key] = message.from_user.id
        logger.info(f"✅ Автор сохранен: {message.from_user.id} для сообщения {key}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {type(e).__name__}: {str(e)}")

# ========== ОБРАБОТКА ВЫБОРА МУТАЦИИ ==========

@router.callback_query(F.data.startswith("mut_"))
async def handle_mutation_selection(callback: types.CallbackQuery):
    """Обработка выбора мутации"""
    # Проверяем автора
    if not await check_author(callback):
        return
    
    logger.info(f"🔘 Выбрана мутация: {callback.data}")
    
    parts = callback.data.split("_")
    if len(parts) != 3:
        logger.error(f"❌ Неправильный формат callback: {callback.data}")
        await callback.answer("❌ Ошибка данных")
        return
    
    mutation_emoji = parts[1]
    number = int(parts[2])
    
    if mutation_emoji not in MUTATIONS:
        logger.error(f"❌ Мутация не найдена: {mutation_emoji}")
        await callback.answer("❌ Мутация не найдена")
        return
    
    mutation = MUTATIONS[mutation_emoji]
    
    # Формируем результат БЕЗ погоды
    result_text = f"🧮 <b>Результаты для {number}</b>\n\n"
    result_text += f"<b>Мутация:</b> {mutation_emoji} {mutation['name']}\n"
    result_text += f"🌤 <b>Погода: Отсутствует</b>\n\n"
    
    for i, percentage in enumerate(mutation["percentages"]):
        weather_name = mutation["names"][i]
        emoji = WEATHER_EMOJIS[weather_name]
        result = int(number + (number * percentage / 100))
        result_text += f"{emoji}<b>{weather_name}:</b> {result} (+{percentage}%)\n"
    
    # Добавляем кнопки выбора погоды
    weather_keyboard = get_weather_keyboard(number, mutation_emoji)
    
    try:
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML",
            reply_markup=weather_keyboard
        )
        logger.info(f"✅ Результат обновлен для мутации {mutation['name']}")
        await callback.answer("✅ Выберите погоду")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления сообщения: {type(e).__name__}: {str(e)}")

# ========== ОБРАБОТКА ВЫБОРА ПОГОДЫ ==========

@router.callback_query(F.data.startswith("weather_"))
async def handle_weather_selection(callback: types.CallbackQuery):
    """Обработка выбора погоды"""
    # Проверяем автора
    if not await check_author(callback):
        return
    
    logger.info(f"☀️ Выбрана погода: {callback.data}")
    
    parts = callback.data.split("_")
    if len(parts) != 4:
        logger.error(f"❌ Неправильный формат callback: {callback.data}")
        await callback.answer("❌ Ошибка данных")
        return
    
    weather_name = parts[1]
    mutation_emoji = parts[2]
    number_with_weather = int(parts[3])
    
    if mutation_emoji not in MUTATIONS:
        logger.error(f"❌ Мутация не найдена: {mutation_emoji}")
        await callback.answer("❌ Мутация не найдена")
        return
    
    mutation = MUTATIONS[mutation_emoji]
    
    # Находим процент выбранной погоды
    weather_index = mutation["names"].index(weather_name)
    weather_percentage = mutation["percentages"][weather_index]
    
    # Вычисляем ИЗНАЧАЛЬНОЕ число БЕЗ погоды
    base_number = int(number_with_weather / (1 + weather_percentage / 100))
    
    weather_emoji = WEATHER_EMOJIS[weather_name]
    
    # Формируем результат С погодой
    result_text = f"🧮 <b>Результаты для {number_with_weather}</b>\n\n"
    result_text += f"<b>Мутация:</b> {mutation_emoji} {mutation['name']}\n"
    result_text += f"{weather_emoji} <b>Погода: {weather_name} (+{weather_percentage}%)</b>\n\n"
    
    for i, percentage in enumerate(mutation["percentages"]):
        current_weather_name = mutation["names"][i]
        emoji = WEATHER_EMOJIS[current_weather_name]
        
        if current_weather_name == weather_name:
            # Это выбранная погода - показываем исходное число
            result_text += f"{emoji}<b>{current_weather_name}:</b> {number_with_weather} (+{percentage}%)\n"
        else:
            # Остальные погоды - считаем от base_number
            result = int(base_number + (base_number * percentage / 100))
            result_text += f"{emoji}<b>{current_weather_name}:</b> {result} (+{percentage}%)\n"
    
    try:
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML"
        )
        logger.info(f"✅ Результат с погодой {weather_name}")
        await callback.answer(f"✅ Погода: {weather_name}")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления сообщения: {type(e).__name__}: {str(e)}")

# ========== КОМАНДА ПОМОЩИ ==========

@router.message(Command("help_group"))
async def help_group_command(message: Message):
    """Команда помощи для группы"""
    if message.chat.type == "private":
        return
    
    logger.info(f"📖 Запрос помощи от {message.from_user.id}")
    
    help_text = (
        "🤖 <b>Команды бота в группе:</b>\n\n"
        "<b>!число</b> - Калькулятор мутаций\n"
        "Примеры: !1000, !500, !25000\n\n"
        "📱 <b>Как использовать:</b>\n"
        "1. Напишите !число (например: !36455)\n"
        "2. Выберите мутацию\n"
        "3. Выберите погоду (Буря/Аврора/Вулкан/Админ)\n"
        "4. Получите результат для всех погод\n\n"
        "📊 <b>Доступные мутации:</b>\n"
        "⚪️ Обычная, 🟡 Золотая, 💎 Алмазная\n"
        "⚡️ Электрическая, 🔥 Огненная, 🦖 Юрская\n"
        "❄️ Снежная, 🎃 Хэллуин, 🦃 Благодарения, 🎄 Рождество, 🌸🩷 День святого Валентина"
    )
    
    await message.answer(help_text, parse_mode="HTML")

# ========== ПРОСТАЯ КОМАНДА ДЛЯ ТЕСТА ==========

@router.message(Command("ping", "test"))
async def ping_command(message: Message):
    """Проверка работы бота"""
    logger.info(f"🏓 Ping команда от {message.from_user.id} в чате {message.chat.type}")
    
    current_time = datetime.now().strftime("%H:%M:%S")
    response = (
        f"🏓 PONG!\n"
        f"🕐 Время: {current_time}\n"
        f"💬 Чат: {message.chat.title or message.chat.type}\n"
        f"👤 Отправитель: {message.from_user.full_name}\n"
        f"✅ Калькулятор мутаций с погодой работает!"
    )
    
    await message.reply(response)
    
@router.message(Command("hide_keyboard"))
async def hide_keyboard(message: Message):
    """Скрыть клавиатуру в группе"""
    from aiogram.types import ReplyKeyboardRemove
    await message.answer(
        "⌨️ Клавиатура скрыта",
        reply_markup=ReplyKeyboardRemove()
    )
