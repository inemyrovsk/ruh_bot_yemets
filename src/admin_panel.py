from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import add_event, change_event, delete_event
import uuid
import os

ADMIN_IDS = [int(id.strip()) for id in os.environ["ADMIN_IDS"].split(',')]

EVENT_DETAILS = range(1)


async def event_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_details = update.message.text
        event_text, event_image = event_details.split('\n')
        event_id = str(uuid.uuid4())  # Generate a unique event ID
        add_event(event_id, event_text, event_image)
        await update.message.reply_photo(photo=event_image, caption=event_text)
        return ConversationHandler.END



async def delete_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id in ADMIN_IDS:
        pass
        # Here you should ask the admin user to confirm the deletion
        # If the admin user confirms the deletion, call the delete_event function to delete the event
        # Then, send a message to the admin user confirming that the event has been deleted

# Add the command handler and callback query handlers to the dispatcher
