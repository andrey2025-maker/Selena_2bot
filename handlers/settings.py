"""
settings.py - Обработчики настроек уведомлений
"""

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from typing import List
import logging

from database import Database
from config import Config
from utils.messages import locale_manager
from utils.keyboards import get_main_keyboard

logger = logging.getLogger(__name__)
router = Router()
db = Database()

# Состояния FSM для выбора фруктов
class FruitSelection(StatesGroup):
    waiting_for_fruits = State()

async def get_user_language(user_id: int) -> str:
    """Получение языка пользователя"""
    user = db.get_user(user_id)
    return user.get("language", "RUS") if user else "RUS"

def get_settings_keyboard(lang: str, user_data: dict = None) -> InlineKeyboardMarkup:
    """Клавиатура настроек"""
    lang_code = "ru" if lang == "RUS" else "en"
    
    # Кнопка выбора фруктов
    food_button = InlineKeyboardButton(
        text=locale_manager.get_text(lang_code, "settings.food_button"),
        callback_data="select_fruits"
    )
    
    # Статус тотемов
    free_status = "✅" if user_data and user_data.get("free_totems", 1) else "❌"
    paid_status = "✅" if user_data and user_data.get("paid_totems", 1) else "❌"
    
    free_button = InlineKeyboardButton(
        text=f"{locale_manager.get_text(lang_code, 'settings.free_totems_button')} {free_status}",
        callback_data="toggle_free"
    )
    
    paid_button = InlineKeyboardButton(
        text=f"{locale_manager.get_text(lang_code, 'settings.paid_totems_button')} {paid_status}",
        callback_data="toggle_paid"
    )
    
    back_button = InlineKeyboardButton(
        text=locale_manager.get_text(lang_code, "settings.back_button"),
        callback_data="back_to_main"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [food_button],
            [free_button],
            [paid_button],
            [back_button]
        ]
    )
    
    return keyboard

def get_fruits_keyboard(lang: str, selected_fruits: List[str] = None) -> InlineKeyboardMarkup:
    """Клавиатура выбора фруктов"""
    if selected_fruits is None:
        selected_fruits = []
    
    lang_code = "ru" if lang == "RUS" else "en"
    keyboard = []
    
    # Кнопка "Выбрать всё"
    select_all_text = locale_manager.get_text(lang_code, "settings.select_all")
    is_all_selected = "all" in selected_fruits
    
    keyboard.append([
        InlineKeyboardButton(
            text=f"{'✅' if is_all_selected else '📦'} {select_all_text}",
            callback_data="select_all_fruits"
        )
    ])
    
    # Кнопки для каждого фрукта
    for fruit_en in Config.AVAILABLE_FRUITS_EN:
        if lang == "RUS":
            fruit_display = Config.FRUIT_TRANSLATIONS.get(fruit_en, fruit_en)
            emoji = Config.FRUIT_EMOJIS_RU.get(fruit_display, "🍎")
        else:
            fruit_display = fruit_en
            emoji = Config.FRUIT_EMOJIS_EN.get(fruit_en, "🍎")
        
        is_selected = "all" in selected_fruits or fruit_en in selected_fruits
        
        button_text = f"{'✅' if is_selected else '☑️'} {emoji} {fruit_display}"
        callback_data = f"fruit_{fruit_en}"
        
        # Располагаем по 2 кнопки в ряд
        if len(keyboard[-1]) < 2 and len(keyboard) > 0:
            keyboard[-1].append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
        else:
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
    
    # Кнопка сохранения
    save_text = locale_manager.get_text(lang_code, "settings.save_button")
    keyboard.append([
        InlineKeyboardButton(text=save_text, callback_data="save_fruits")
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("settings"))
async def cmd_settings(message: Message):
    """Команда /settings - открыть настройки"""
    user_id = message.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    user = db.get_user(user_id)
    if not user:
        await message.answer("❌ Пользователь не найден. Используйте /start")
        return
    
    # Получаем выбранные фрукты
    user_fruits = db.get_user_fruits(user_id)
    
    # Формируем текст о текущих настройках
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
    
    await message.answer(
        settings_text,
        reply_markup=get_settings_keyboard(lang, user),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "select_fruits")
async def select_fruits(callback: CallbackQuery, state: FSMContext):
    """Начало выбора фруктов"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    # Получаем текущие выбранные фрукты
    user_fruits = db.get_user_fruits(user_id)
    
    await state.set_state(FruitSelection.waiting_for_fruits)
    await state.update_data(selected_fruits=user_fruits)
    
    await callback.message.edit_text(
        locale_manager.get_text(lang_code, "settings.food_selection"),
        reply_markup=get_fruits_keyboard(lang, user_fruits)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("fruit_"))
async def toggle_fruit(callback: CallbackQuery, state: FSMContext):
    """Выбор/отмена выбора фрукта"""
    fruit_en = callback.data.replace("fruit_", "")
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем текущее состояние
    data = await state.get_data()
    selected_fruits = data.get("selected_fruits", [])
    
    # Если выбран "all", очищаем список
    if "all" in selected_fruits:
        selected_fruits.remove("all")
    
    # Переключаем фрукт
    if fruit_en in selected_fruits:
        selected_fruits.remove(fruit_en)
    else:
        selected_fruits.append(fruit_en)
    
    # Обновляем состояние
    await state.update_data(selected_fruits=selected_fruits)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_fruits_keyboard(lang, selected_fruits)
    )
    await callback.answer()

@router.callback_query(F.data == "select_all_fruits")
async def select_all_fruits(callback: CallbackQuery, state: FSMContext):
    """Выбрать все фрукты"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем текущее состояние
    data = await state.get_data()
    selected_fruits = data.get("selected_fruits", [])
    
    # Переключаем режим "все"
    if "all" in selected_fruits:
        selected_fruits = []
    else:
        selected_fruits = ["all"]
    
    # Обновляем состояние
    await state.update_data(selected_fruits=selected_fruits)
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=get_fruits_keyboard(lang, selected_fruits)
    )
    await callback.answer()

@router.callback_query(F.data == "save_fruits")
async def save_fruits_selection(callback: CallbackQuery, state: FSMContext):
    """Сохранение выбранных фруктов"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    lang_code = "ru" if lang == "RUS" else "en"
    
    # Получаем выбранные фрукты из состояния
    data = await state.get_data()
    selected_fruits = data.get("selected_fruits", [])
    
    # Сохраняем в БД
    db.update_user_fruits(user_id, selected_fruits)
    
    # Очищаем состояние
    await state.clear()
    
    # Формируем текст о сохраненных настройках
    if selected_fruits:
        if "all" in selected_fruits:
            fruits_text = "📦 Все фрукты"
        else:
            fruit_names = []
            for fruit in selected_fruits:
                display = locale_manager.get_fruit_display(fruit, lang)
                fruit_names.append(display)
            fruits_text = ", ".join(fruit_names)
    else:
        fruits_text = locale_manager.get_text(lang_code, "settings.no_fruits_selected")
    
    # Удаляем сообщение с выбором фруктов
    await callback.message.delete()
    
    # Отправляем подтверждение и возвращаем главное меню
    await callback.message.answer(
        locale_manager.get_text(lang_code, "settings.saved").format(fruits=fruits_text),
        reply_markup=get_main_keyboard(lang)
    )
    await callback.answer()

@router.callback_query(F.data == "toggle_free")
async def toggle_free_totems(callback: CallbackQuery):
    """Переключение уведомлений о бесплатных тотемах"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем текущие настройки
    user = db.get_user(user_id)
    current_status = user.get("free_totems", 1)
    
    # Переключаем статус
    db.update_totem_settings(user_id, free_totems=not current_status)
    
    # Обновляем пользователя
    user = db.get_user(user_id)
    
    # Обновляем сообщение
    await callback.message.edit_reply_markup(
        reply_markup=get_settings_keyboard(lang, user)
    )
    await callback.answer()

@router.callback_query(F.data == "toggle_paid")
async def toggle_paid_totems(callback: CallbackQuery):
    """Переключение уведомлений о платных тотемах"""
    user_id = callback.from_user.id
    lang = await get_user_language(user_id)
    
    # Получаем текущие настройки
    user = db.get_user(user_id)
    current_status = user.get("paid_totems", 1)
    
    # Переключаем статус
    db.update_totem_settings(user_id, paid_totems=not current_status)
    
    # Обновляем пользователя
    user = db.get_user(user_id)
    
    # Обновляем сообщение
    await callback.message.edit_reply_markup(
        reply_markup=get_settings_keyboard(lang, user)
    )
    await callback.answer()
