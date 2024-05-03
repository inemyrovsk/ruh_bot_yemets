from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, \
    InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler
from database import check_user_registered, add_user, add_user_to_event, add_event
import uuid
import os

ADMIN_IDS = [534616491, 987654321]

bot_usage_help = """
🌟 Welcome to Ruh Event Bot! 🌟

Quick Guide:

Register: Start by sharing your phone number and name to register.
Join Events: Tap the "Join" button on event announcements to register. You'll receive confirmation and reminders.
Support: Use the "Write to support" button for any questions or help.
Ready to explore and join exciting events? Start by sending us a message!
"""


async def share_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not check_user_registered(user.id):
        await update.message.reply_text(
            f"Hi {user.first_name}, you need to register before you can use this bot. Please share your contact."
        )
        contact_keyboard = KeyboardButton(text="Share My Contact", request_contact=True)
        custom_keyboard = [[contact_keyboard]]

        if user.id in ADMIN_IDS:
            admin_button = KeyboardButton(text="Admin")
            custom_keyboard.append([admin_button])

        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Click the button below to share your contact.",
            reply_markup=reply_markup
        )
    else:

        events_button = KeyboardButton(text="Show all Events")
        custom_keyboard = [[events_button]]

        if user.id in ADMIN_IDS:
            admin_button = KeyboardButton(text="Admin")
            custom_keyboard.append([admin_button])

        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            bot_usage_help,
            reply_markup=reply_markup
        )


exception_message = "An error occurred while registering you. Please try again or Message Support."


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.effective_message.contact
    user = update.effective_user
    if not check_user_registered(contact.user_id):
        try:
            add_user(contact.user_id, contact.phone_number, contact.first_name)
            events_button = KeyboardButton(text="Show all Events")
            custom_keyboard = [[events_button]]

            if user.id in ADMIN_IDS:
                admin_button = KeyboardButton(text="Admin")
                custom_keyboard.append([admin_button])

            reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
            await update.message.reply_text(
                bot_usage_help,
                reply_markup=reply_markup
            )
        except:
            await update.message.reply_text(exception_message)
            return


async def send_event_announcement(update: Update, context: ContextTypes.DEFAULT_TYPE, event_id, event_text,
                                  event_image):
    join_button = InlineKeyboardButton("Join", callback_data=f'join_{event_id}')
    reply_markup = InlineKeyboardMarkup([[join_button]])

    await update.message.reply_photo(
        photo=event_image,
        caption=event_text,
        reply_markup=reply_markup
    )


async def join_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = query.data.split('_')[1]
    user_id = update.effective_user.id

    add_user_to_event(user_id, event_id)

    await query.answer("You have joined the event!")


EVENT_TEXT, EVENT_IMAGE, EVENT_TIME, EVENT_LOCATION, EVENT_CONFIRMATION = range(5)


async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        create_event_button = KeyboardButton(text="Create Event")
        change_event_button = KeyboardButton(text="Change Event")
        delete_event_button = KeyboardButton(text="Delete Event")
        custom_keyboard = [[create_event_button, change_event_button, delete_event_button]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Choose an action.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("You are not authorized to perform this action.")


def back_and_cancel_button():
    back_button = KeyboardButton(text="Back")
    cancel_button = KeyboardButton(text="Cancel")
    custom_keyboard = [[back_button, cancel_button]]
    reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
    return reply_markup


async def create_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_id = str(uuid.uuid4())
        context.user_data['event_id'] = event_id
        await update.message.reply_text(
            f"Event ID: {event_id}\nPlease reply with the event text.",
            reply_markup=back_and_cancel_button()
        )
        return EVENT_TEXT


async def event_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_text = update.message.text
        context.user_data['event_text'] = event_text
        context.user_data['previous_state'] = EVENT_TEXT
        await update.message.reply_text(
            "Please upload the event image.", reply_markup=back_and_cancel_button())
        return EVENT_IMAGE


async def event_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        photo = update.message.photo[-1]  # Get the highest resolution photo
        file = await context.bot.get_file(photo.file_id)

        # Define the local path where you want to store the image
        local_image_path = os.path.join('images', f"{file.file_id}.jpg")
        await file.download_to_drive(custom_path=local_image_path)

        # Save the local path of the image in context.user_data
        context.user_data['event_image'] = local_image_path
        context.user_data['previous_state'] = EVENT_IMAGE
        reply_markup = back_and_cancel_button()
        await update.message.reply_text(
            "Please enter the event time.", reply_markup=reply_markup)
        return EVENT_TIME


async def event_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_time = update.message.text
        context.user_data['event_time'] = event_time
        reply_markup = back_and_cancel_button()

        await update.message.reply_text("Please enter the event location.", reply_markup=reply_markup)
        return EVENT_LOCATION


async def event_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_location = update.message.text
        context.user_data['event_location'] = event_location
        event_id = context.user_data['event_id']
        event_text = context.user_data['event_text']
        event_image_path = context.user_data['event_image']
        event_time = context.user_data['event_time']
        event_text = f"{event_text}\n\nTime: {event_time}\nLocation: {event_location}\n event_id: {event_id}"
        await update.message.reply_photo(photo=event_image_path, caption=event_text)
        await update.message.reply_text("Do you want to add this event to the database? (yes/no)")
        return EVENT_CONFIRMATION


async def event_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        if update.message.text.lower() == 'yes':
            event_id = context.user_data['event_id']
            event_text = context.user_data['event_text']
            event_image_path = context.user_data['event_image']
            event_time = context.user_data['event_time']
            event_location = context.user_data['event_location']

            events_button = KeyboardButton(text="Show all Events")
            custom_keyboard = [[events_button]]
            reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)

            if update.effective_user.id in ADMIN_IDS:
                admin_button = KeyboardButton(text="Admin")
                custom_keyboard.append([admin_button])

            add_event(event_id, event_text, event_image_path, event_time, event_location)
            await update.message.reply_text("Event added to the database.", reply_markup=reply_markup)
            return ConversationHandler.END
        else:
            return EVENT_LOCATION


async def back_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    previous_state = context.user_data.get('previous_state', ConversationHandler.END)
    await query.answer()
    return previous_state


async def cancel_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("Are you sure you want to cancel the event creation? (yes/no)")


async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'yes':
        user = update.effective_user
        await update.message.reply_text(f'Event creation cancelled by {user.first_name}.')
        return ConversationHandler.END
    else:
        previous_state = context.user_data.get('previous_state', ConversationHandler.END)
        return previous_state


conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^Create Event$'), create_event_callback)],
    states={
        EVENT_TEXT: [MessageHandler(filters.TEXT, event_text)],
        EVENT_IMAGE: [MessageHandler(filters.PHOTO, event_image)],
        EVENT_TIME: [MessageHandler(filters.TEXT, event_time)],
        EVENT_LOCATION: [MessageHandler(filters.TEXT, event_location)],
        EVENT_CONFIRMATION: [MessageHandler(filters.TEXT, event_confirmation)],
    },
    fallbacks=[
        CallbackQueryHandler(back_button_callback, pattern='^back$'),
        CallbackQueryHandler(cancel_button_callback, pattern='^cancel$'),
        MessageHandler(filters.TEXT & (~filters.COMMAND), confirm_cancel)
    ]
)
