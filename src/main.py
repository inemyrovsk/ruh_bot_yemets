import os

from telegram import KeyboardButton, Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler, \
    ConversationHandler
import handlers
from events import show_events, navigate_event, register_button_callback, change_event_request, change_event_detail, \
    receive_new_event_details, approve_changes, show_joined_users, delete_event_request, contact_support
from database import initialize_db

BOT_TOKEN = os.environ["BOT_TOKEN"]


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(handlers.registration_conv_handler)
    application.add_handler(MessageHandler(filters.Regex('^Admin$'), handlers.admin_handler))
    application.add_handler(MessageHandler(filters.Regex('^Show all Events'), show_events))
    application.add_handler(MessageHandler(filters.Regex('^Підтримка'), contact_support))
    application.add_handler(CallbackQueryHandler(navigate_event, pattern='^(next_event|previous_event)$'))
    application.add_handler(handlers.conv_handler)
    application.add_handler(CallbackQueryHandler(register_button_callback, pattern='^join_'))
    application.add_handler(CallbackQueryHandler(show_joined_users, pattern='^show_joined_'))
    application.add_handler(CallbackQueryHandler(change_event_request, pattern='^change_event_'))
    application.add_handler(CallbackQueryHandler(delete_event_request, pattern='^delete_event_'))
    application.add_handler(CallbackQueryHandler(change_event_detail, pattern='^change_(name|time|image|location|price)_'))
    application.add_handler(MessageHandler(filters.TEXT | filters.PHOTO & ~filters.COMMAND, receive_new_event_details))
    application.add_handler(CallbackQueryHandler(approve_changes, pattern='^approve_changes_'))

    application.run_polling()


def main_buttons(admin=False):
    events_button = KeyboardButton(text="Show all Events")
    custom_keyboard = [[events_button]]

    if admin:
        admin_button = KeyboardButton(text="Admin")
        custom_keyboard.append([admin_button])
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
    return reply_markup


def change_event_buttons(event_id):
    buttons = [[InlineKeyboardButton("Change Text", callback_data=f"change_name_{event_id}")],
               [InlineKeyboardButton("Change Image", callback_data=f"change_image_{event_id}")],
               [InlineKeyboardButton("Change Time", callback_data=f"change_time_{event_id}")],
               [InlineKeyboardButton("Change Location", callback_data=f"change_location_{event_id}")],
               [InlineKeyboardButton("Change Price", callback_data=f"change_price_{event_id}")],
               [InlineKeyboardButton("Approve Changes", callback_data=f"approve_changes_{event_id}")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    return reply_markup


if __name__ == '__main__':
    initialize_db()
    main()
