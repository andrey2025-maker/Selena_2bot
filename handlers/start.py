"""
start.py - Обработчик команды /start и проверки подписки
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from database import Database
from utils.messages import locale_manager
from utils.keyboards import get_main_keyboard
from utils.subscription import check_user_subscription
from config import Config
import logging

router = Router()
db = Database()
logger = logging.getLogger(__name__)

async def get_user_language(user_id: int) -> str:
    """Получение языка пользователя"""
    user = db.get_user(user_id)
    return user.get("language", "RUS") if user else "RUS"

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.chat.type != "private":
        return
    """Обработка команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    
    # Добавляем пользователя в БД
    db.add_user(user_id, username)
    logger.info(f"Пользователь {user_id} запустил бота")
    
    # Текст на двух языках
    text = (
        f"{locale_manager.get_text('ru', 'start.welcome')}\n"
        f"{locale_manager.get_text('ru', 'start.choose_language')}\n\n"
        f"{locale_manager.get_text('en', 'start.welcome')}\n"
        f"{locale_manager.get_text('en', 'start.choose_language')}"
    )
    
    # Клавиатура выбора языка
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🇷🇺 Русский", callback_data="lang_rus")
    builder.button(text="🇺🇸 English", callback_data="lang_en")
    builder.adjust(2)
    
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.in_(["lang_rus", "lang_en"]))
async def set_language(callback: CallbackQuery):
    """Установка языка после выбора"""
    user_id = callback.from_user.id
    lang = "RUS" if callback.data == "lang_rus" else "EN"
    
    # Сохраняем язык в БД
    db.update_user_language(user_id, lang)
    lang_code = "ru" if lang == "RUS" else "en"
    
    logger.info(f"Пользователь {user_id} выбрал язык: {lang}")
    
    # Удаляем сообщение с выбором языка
    await callback.message.delete()
    
    # Проверяем подписку
    is_subscribed = await check_user_subscription(
        user_id, 
        Config.REQUIRED_GROUP_ID, 
        callback.bot
    )
    
    is_exception = db.is_exception(user_id)
    
    if is_subscribed or is_exception:
        # Уже подписан - показываем настройки и главную клавиатуру
        await show_settings_menu(callback.message, user_id, lang, lang_code, callback.bot)
    else:
        # Требуется подписка
        require_text = locale_manager.get_text(lang_code, "subscription.require")
        check_button_text = locale_manager.get_text(lang_code, "subscription.check_button")
        
        # Клавиатура с кнопкой проверки
        check_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=check_button_text)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await callback.message.answer(
            require_text,
            reply_markup=check_keyboard
        )
    
    await callback.answer()

@router.message(F.text.in_(["🔍 Проверить подписку", "🔍 Check subscription"]))
async def check_subscription(message: Message):
    if message.chat.type != "private":
        return
    """Проверка подписки по кнопке"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    logger.info(f"Пользователь {user_id} проверяет подписку")
    
    is_subscribed = await check_user_subscription(
        user_id, 
        Config.REQUIRED_GROUP_ID, 
        message.bot
    )
    
    is_exception = db.is_exception(user_id)
    
    if is_subscribed or is_exception:
        # Подписка подтверждена - показываем настройки
        await show_settings_menu(message, user_id, lang, lang_code, message.bot)
    else:
        # Не подписан
        not_subscribed_text = locale_manager.get_text(lang_code, "subscription.not_subscribed")
        check_button_text = locale_manager.get_text(lang_code, "subscription.check_button")
        
        # Показываем снова кнопку проверки
        check_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=check_button_text)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            not_subscribed_text,
            reply_markup=check_keyboard
        )

async def show_settings_menu(message: Message, user_id: int, lang: str, lang_code: str, bot):
    """Показывает меню настроек (одно сообщение с кнопками)"""
    
    # Получаем текущие настройки пользователя
    user = db.get_user(user_id)
    user_fruits = db.get_user_fruits(user_id)
    
    # Формируем текст о текущих настройках
    fruits_text = ""
    if user_fruits:
        if "all" in user_fruits:
            fruits_text = "📦 Все фрукты"
        else:
            fruit_names = []
            for fruit in user_fruits:
                display = locale_manager.get_fruit_display(fruit, lang)
                fruit_names.append(display)
            fruits_text = ", ".join(fruit_names)
    else:
        fruits_text = locale_manager.get_text(lang_code, "settings.no_fruits_selected")
    
    free_status = "✅" if user.get("free_totems", 1) else "❌"
    paid_status = "✅" if user.get("paid_totems", 1) else "❌"
    
    settings_text = locale_manager.get_text(lang_code, "settings.title")
    settings_text += f"\n\n📋 <b>Текущие настройки:</b>\n🥝 Фрукты: {fruits_text}\n🗿 Free: {free_status}\n💎 Paid: {paid_status}"
    
    from handlers.settings import get_settings_keyboard
    
    # Потом показываем настройки с инлайн-кнопками
    await message.answer(
        settings_text,
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(lang, user)
    )

@router.message(F.text.in_(["🔔 Уведомления", "🔔 Notifications"]))
async def show_notifications_menu(message: Message):
    if message.chat.type != "private":
        return
    """Показ меню уведомлений"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    # Проверяем подписку
    is_subscribed = await check_user_subscription(
        user_id, 
        Config.REQUIRED_GROUP_ID, 
        message.bot
    )
    
    if not is_subscribed and not db.is_exception(user_id):
        not_subscribed_text = locale_manager.get_text(lang_code, "subscription.not_subscribed")
        check_button_text = locale_manager.get_text(lang_code, "subscription.check_button")
        
        check_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=check_button_text)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        
        await message.answer(
            not_subscribed_text,
            reply_markup=check_keyboard
        )
        return
    
    # Получаем текущие настройки пользователя
    user = db.get_user(user_id)
    user_fruits = db.get_user_fruits(user_id)
    
    # Формируем текст о текущих настройках
    fruits_text = ""
    if user_fruits:
        if "all" in user_fruits:
            fruits_text = "📦 Все фрукты"
        else:
            fruit_names = []
            for fruit in user_fruits:
                display = locale_manager.get_fruit_display(fruit, lang)
                fruit_names.append(display)
            fruits_text = ", ".join(fruit_names)
    else:
        fruits_text = locale_manager.get_text(lang_code, "settings.no_fruits_selected")
    
    free_status = "✅" if user.get("free_totems", 1) else "❌"
    paid_status = "✅" if user.get("paid_totems", 1) else "❌"
    
    settings_text = locale_manager.get_text(lang_code, "settings.title")
    settings_text += f"\n\n📋 <b>Текущие настройки:</b>\n🥝 Фрукты: {fruits_text}\n🗿 Free: {free_status}\n💎 Paid: {paid_status}"
    
    from handlers.settings import get_settings_keyboard
    
    # Показываем настройки с инлайн-кнопками (главная клавиатура уже есть)
    await message.answer(
        settings_text,
        parse_mode="HTML",
        reply_markup=get_settings_keyboard(lang, user)
    )

@router.message(F.text.in_(["🔕 Отключить", "🔕 Disable"]))
async def disable_notifications(message: Message):
    if message.chat.type != "private":
        return
    """Полное отключение всех уведомлений"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    
    # Отключаем все уведомления
    db.update_user_fruits(user_id, [])
    db.update_totem_settings(user_id, free_totems=False, paid_totems=False)
    
    if lang == "RUS":
        text = "✅ Все уведомления отключены!\nЧтобы снова включить, нажмите «🔔 Уведомления»"
    else:
        text = "✅ All notifications disabled!\nTo enable again, click «🔔 Notifications»"
    
    await message.answer(
        text,
        reply_markup=get_main_keyboard(lang)
    )

@router.message(F.text.in_(["❓ Помощь", "❓ Help"]))
async def show_help(message: Message):
    if message.chat.type != "private":
        return
    """Показ справки"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    help_text = {
        "ru": """
❓ <b>Помощь по боту</b>

🔔 <b>Уведомления</b> - настройка фруктов и тотемов
🔕 <b>Отключить</b> - полностью отключить все уведомления

<b>Доступные команды:</b>
/start - перезапустить бота
/settings - настройки уведомлений
/language - смена языка

<b>Как это работает:</b>
1. Бот отслеживает сообщения в канале-источнике
2. При появлении фрукта - отправляет уведомление подписанным пользователям
3. При появлении тотема с ссылкой Roblox - отправляет уведомление

<b>Поддержка:</b>
По вопросам: @админ
        """,
        "en": """
❓ <b>Bot Help</b>

🔔 <b>Notifications</b> - configure fruits and totems
🔕 <b>Disable</b> - completely disable all notifications

<b>Available commands:</b>
/start - restart bot
/settings - notification settings
/language - change language

<b>How it works:</b>
1. Bot monitors messages in the source channel
2. When fruit appears - sends notification to subscribed users
3. When totem with Roblox link appears - sends notification

<b>Support:</b>
Contact: @admin
        """
    }
    
    await message.answer(
        help_text[lang_code],
        parse_mode="HTML",
        reply_markup=get_main_keyboard(lang)
    )

@router.message(Command("language"))
async def cmd_language(message: Message):
    """Команда для смены языка"""
    user_id = message.from_user.id
    
    language_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_rus")],
        [InlineKeyboardButton(text="🇺🇸 English", callback_data="lang_en")]
    ])
    
    await message.answer(
        "🇷🇺 Выберите язык:\n🇺🇸 Choose language:",
        reply_markup=language_keyboard
    )
