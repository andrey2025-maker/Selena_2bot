"""
group_commands.py - Команды для работы в группах
ПОЛНОСТЬЮ ИСПРАВЛЕННАЯ РАБОЧАЯ ВЕРСИЯ
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
    }
}

# ========== ЭМОДЗИ ДЛЯ РЕЗУЛЬТАТОВ ==========
RESULT_EMOJIS = {
    "Буря": "💨",
    "Аврора": "🌀", 
    "Вулкан": "🌋",
    "Админ": "🪯"
}

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
        
        # 2 кнопки в ряду
        if i % 2 == 0:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ========== ОСНОВНЫЕ КОМАНДЫ - ИСПРАВЛЕННЫЙ ФИЛЬТР ==========

@router.message(F.text, F.chat.type.in_(["group", "supergroup"]))
async def handle_group_messages(message: Message):
    """Обработка ВСЕХ сообщений в группах"""
    if not message.text:
        return
    
    text = message.text.strip()
    logger.info(f"📨 ГРУППА: Получено сообщение в группе '{message.chat.id}': '{text}'")
    
    # Проверяем команду !число
    if text.startswith('!'):
        await handle_exclamation_command(message, text)

# ========== ОБРАБОТКА КОМАНД С ! ==========

async def handle_exclamation_command(message: Message, text: str):
    """Обработка команд с !"""
    logger.info(f"🔧 Обработка команды с !: '{text}'")
    
    # Проверяем формат !число
    match = re.match(r'^!(\d+)$', text)
    if not match:
        logger.warning(f"❌ Неправильный формат команды: {text}")
        return
    
    number = int(match.group(1))
    logger.info(f"✅ Формат правильный! Число: {number}")
    
    # Создаем клавиатуру
    keyboard = get_mutation_keyboard(number)
    
    # Отправляем сообщение с клавиатурой
    try:
        logger.info(f"🔄 Отправляю ответ для !{number}...")
        sent_message = await message.reply(
            f"🧮 <b>Калькулятор мутаций</b>\n\n"
            f"<b>Число:</b> {number}\n"
            f"<b>Выберите мутацию:</b>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logger.info(f"✅ Ответ успешно отправлен! ID сообщения: {sent_message.message_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки: {type(e).__name__}: {str(e)}")
        # Резервный вариант - простой ответ без клавиатуры
        try:
            await message.answer(
                f"🧮 <b>Калькулятор для {number}</b>\n\n"
                f"⚪️ <b>Обычная мутация:</b>\n"
                f"💨 Буря: {number * 2} (+100%)\n"
                f"🌀 Аврора: {number * 3} (+200%)\n"
                f"🌋 Вулкан: {number * 4} (+300%)\n"
                f"🪯 Админ: {number * 5} (+400%)\n\n"
                f"<i>Для других мутаций используйте инлайн-клавиатуру</i>",
                parse_mode="HTML"
            )
            logger.info("✅ Простой ответ отправлен")
        except Exception as e2:
            logger.error(f"❌ Ошибка отправки простого ответа: {e2}")

# ========== ОБРАБОТКА ВЫБОРА МУТАЦИИ ==========

@router.callback_query(F.data.startswith("mut_"))
async def handle_mutation_selection(callback: types.CallbackQuery):
    """Обработка выбора мутации из инлайн-клавиатуры"""
    logger.info(f"🔘 Нажата кнопка: {callback.data}")
    
    # Парсим данные: mut_⚪️_36455
    parts = callback.data.split("_")
    if len(parts) != 3:
        logger.error(f"❌ Неправильный формат callback: {callback.data}")
        await callback.answer("❌ Ошибка данных")
        return
    
    emoji = parts[1]
    number = int(parts[2])
    
    if emoji not in MUTATIONS:
        logger.error(f"❌ Мутация не найдена: {emoji}")
        await callback.answer("❌ Мутация не найдена")
        return
    
    mutation = MUTATIONS[emoji]
    logger.info(f"✅ Выбрана мутация: {mutation['name']} для числа {number}")
    
    # Формируем результат
    result_text = f"🧮 <b>Результаты для {number}</b>\n\n"
    result_text += f"<b>Мутация:</b> {emoji} {mutation['name']}\n\n"
    
    for i, percentage in enumerate(mutation["percentages"]):
        result = number + (number * percentage / 100)
        emoji_result = RESULT_EMOJIS.get(mutation["names"][i], "⭐")
        result_text += f"{emoji_result}<b>{mutation['names'][i]}:</b> {int(result)} (+{percentage}%)\n"
    
    # Отправляем результат
    try:
        await callback.message.edit_text(
            result_text,
            parse_mode="HTML"
        )
        logger.info(f"✅ Результат обновлен для мутации {mutation['name']}")
        await callback.answer("✅ Расчет завершен")
    except Exception as e:
        logger.error(f"❌ Ошибка обновления сообщения: {type(e).__name__}: {str(e)}")
        # Попробуем отправить новое сообщение
        try:
            await callback.message.answer(result_text, parse_mode="HTML")
            await callback.answer("✅ Результат отправлен в новом сообщении")
        except Exception as e2:
            logger.error(f"❌ Не удалось отправить результат: {e2}")
            await callback.answer("❌ Ошибка отправки")

# ========== КОМАНДА ПОМОЩИ ==========

@router.message(Command("help_group"))
async def help_group_command(message: Message):
    """Команда помощи для группы"""
    # Проверяем, что команда только в группах
    if message.chat.type == "private":
        return
    
    logger.info(f"📖 Запрос помощи от {message.from_user.id}")
    
    help_text = (
        "🤖 <b>Команды бота в группе:</b>\n\n"
        "<b>!число</b> - Калькулятор мутаций\n"
        "Примеры: !1000, !500, !25000\n\n"
        "📱 <b>Как использовать:</b>\n"
        "1. Напишите !число (например: !36455)\n"
        "2. Выберите мутацию из кнопок\n"
        "3. Получите расчет для всех 4 уровней\n\n"
        "📊 <b>Доступные мутации:</b>\n"
        "⚪️ Обычная, 🟡 Золотая, 💎 Алмазная\n"
        "⚡️ Электрическая, 🔥 Огненная, 🦖 Юрская\n"
        "❄️ Снежная, 🎃 Хэллуин, 🦃 Благодарения, 🎄 Рождество"
    )
    
    await message.answer(help_text, parse_mode="HTML")

# ========== ПРОСТАЯ КОМАНДА ДЛЯ ТЕСТА ==========

@router.message(Command("ping", "test"))
async def ping_command(message: Message):
    """Проверка работы бота в группе"""
    if message.chat.type == "private":
        return
    
    logger.info(f"🏓 Ping команда от {message.from_user.id}")
    
    # Добавляем информацию о времени и чате
    current_time = datetime.now().strftime("%H:%M:%S")
    response = (
        f"🏓 PONG!\n"
        f"🕐 Время: {current_time}\n"
        f"💬 Чат: {message.chat.title or message.chat.id}\n"
        f"👤 Отправитель: {message.from_user.full_name}\n"
        f"✅ Калькулятор мутаций работает!"
    )
    
    await message.reply(response)

# ========== ОБРАБОТКА ЛЮБЫХ ДРУГИХ СООБЩЕНИЙ В ГРУППЕ ==========

@router.message(F.chat.type.in_(["group", "supergroup"]))
async def handle_other_messages(message: Message):
    """Обработка других сообщений в группе (для отладки)"""
    # Не логируем все сообщения, только если нужно
    # logger.debug(f"📨 Группа {message.chat.id}: {message.from_user.id}: {message.text}")
    pass