"""
keyboards.py - Постоянные клавиатуры для бота
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_keyboard(language: str = "RUS") -> ReplyKeyboardMarkup:
    """
    Основная клавиатура с кнопками:
    - Уведомления
    - Отключить
    - Помощь
    """
    builder = ReplyKeyboardBuilder()
    
    if language == "RUS":
        buttons = [
            KeyboardButton(text="🔔 Уведомления"),
            KeyboardButton(text="🔕 Отключить"),
            KeyboardButton(text="❓ Помощь")
        ]
    else:
        buttons = [
            KeyboardButton(text="🔔 Notifications"),
            KeyboardButton(text="🔕 Disable"),
            KeyboardButton(text="❓ Help")
        ]
    
    builder.row(*buttons, width=3)
    
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=False)

def remove_keyboard() -> ReplyKeyboardRemove:
    """Удаление клавиатуры"""
    return ReplyKeyboardRemove()
