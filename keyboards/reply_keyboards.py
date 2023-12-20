from aiogram.types import ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_check_email_keyboards() -> ReplyKeyboardMarkup:
    markup = ReplyKeyboardBuilder()

    markup.button(text='Да')
    markup.button(text='Исправить')

    return markup.as_markup(resize_keyboard=True, one_time_keyboard=True)
