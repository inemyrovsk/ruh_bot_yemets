from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, \
    InputMediaPhoto
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters, CallbackQueryHandler, \
    CommandHandler
from database import check_user_registered, add_user, add_user_to_event, add_event
import uuid
import os
import main

ADMIN_IDS = [int(id.strip()) for id in os.environ["ADMIN_IDS"].split(',')]
# [534616491, 987654321]
bot_usage_help = """
🌟 Welcome to Ruh Event Bot! 🌟

Quick Guide:

Register: Start by sharing your phone number and name to register.
Join Events: Tap the "Join" button on event announcements to register. You'll receive confirmation and reminders.
Support: Use the "Write to support" button for any questions or help.
Ready to explore and join exciting events? Start by sending us a message!
"""

SHARE_CONTACT, REQUEST_NAME = range(2)


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
        return SHARE_CONTACT
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
        return ConversationHandler.END


exception_message = "An error occurred while registering you. Please try again or Message Support."


async def contact_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    contact = update.effective_message.contact
    context.user_data['phone_number'] = contact.phone_number
    if not check_user_registered(contact.user_id):
        await update.message.reply_text("Thanks! Now please enter your name:")
        return REQUEST_NAME


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = update.message.text
    phone_number = context.user_data['phone_number']  # Retrieve phone number from context
    add_user(user.id, phone_number, name)
    await update.message.reply_text("Thank you for registering!", reply_markup=main.main_buttons(user.id in ADMIN_IDS))
    return ConversationHandler.END


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
        custom_keyboard = [[create_event_button]]
        reply_markup = ReplyKeyboardMarkup(custom_keyboard, one_time_keyboard=True, resize_keyboard=True)
        await update.message.reply_text(
            f"Choose an action.",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("You are not authorized to perform this action.")


def back_and_cancel_button(event_confirmation=False):
    back_button = InlineKeyboardButton("Back", callback_data="back")
    cancel_button = InlineKeyboardButton("Cancel", callback_data="cancel")
    reply_markup = InlineKeyboardMarkup([[back_button, cancel_button]])
    if event_confirmation:
        confirm_button = InlineKeyboardButton("Confirm", callback_data="confirm")
        reply_markup = InlineKeyboardMarkup([[back_button, cancel_button, confirm_button]])
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
        context.user_data['previous_state'] = EVENT_TIME
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
        context.user_data['previous_state'] = EVENT_LOCATION
        event_text = f"{event_text}\n\nTime: {event_time}\nLocation: {event_location}\n event_id: {event_id}"
        await update.message.reply_photo(photo=event_image_path, caption=event_text, reply_markup=back_and_cancel_button(event_confirmation=True))
        return EVENT_CONFIRMATION


async def event_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    ADMIN = bool(update.effective_user.id in ADMIN_IDS)
    if ADMIN:
        if query.data == 'confirm':
            event_id = context.user_data['event_id']
            event_text = context.user_data['event_text']
            event_image_path = context.user_data['event_image']
            event_time = context.user_data['event_time']
            event_location = context.user_data['event_location']
            context.user_data['previous_state'] = EVENT_CONFIRMATION
            reply_markup = main.main_buttons(ADMIN)

            add_event(event_id, event_text, event_image_path, event_time, event_location)
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Event added to the database.",
                                           reply_markup=reply_markup)
            return ConversationHandler.END


async def back_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    previous_state = context.user_data.get('previous_state', EVENT_TEXT)  # Default to EVENT_TEXT if not found

    if previous_state == EVENT_TEXT:
        await query.edit_message_text(
            "Please enter the text for the event:",
            reply_markup=back_and_cancel_button()
        )
    elif previous_state == EVENT_IMAGE:
        await query.edit_message_text(
            "Please upload the event image:",
            reply_markup=back_and_cancel_button()
        )
    elif previous_state == EVENT_TIME:
        await query.edit_message_text(
            "Please enter the event time:",
            reply_markup=back_and_cancel_button()
        )
    elif previous_state == EVENT_LOCATION:
        await query.edit_message_text(
            "Please enter the event location:",
            reply_markup=back_and_cancel_button()
        )

    return previous_state


async def cancel_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Are you sure you want to cancel the event creation? (yes/no)")


async def confirm_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.lower() == 'yes':
        await update.message.reply_text(f'Event creation cancelled.')
        return ConversationHandler.END
    else:
        # Redirect them back to the previous state or the start of the conversation
        previous_state = context.user_data.get('previous_state', EVENT_TEXT)
        return previous_state


registration_conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", share_contact)],
    states={
        SHARE_CONTACT: [MessageHandler(filters.CONTACT, contact_handler)],
        REQUEST_NAME: [MessageHandler(filters.TEXT, name_handler)],

    },
    fallbacks=[CommandHandler('cancel', lambda update, context: update.message.reply_text('Registration cancelled.'))]
)


conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex('^Create Event$'), create_event_callback)],
    states={
        EVENT_TEXT: [MessageHandler(filters.TEXT, event_text)],
        EVENT_IMAGE: [MessageHandler(filters.PHOTO, event_image)],
        EVENT_TIME: [MessageHandler(filters.TEXT, event_time)],
        EVENT_LOCATION: [MessageHandler(filters.TEXT, event_location)],
        EVENT_CONFIRMATION: [CallbackQueryHandler(event_confirmation, pattern='^confirm$')]
    },
    fallbacks=[
        CallbackQueryHandler(back_button_callback, pattern='^back$'),
        CallbackQueryHandler(cancel_button_callback, pattern='^cancel$'),
        MessageHandler(filters.TEXT & (~filters.COMMAND), confirm_cancel)
    ]
)
