from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from database import add_event, change_event, delete_event
import uuid

ADMIN_IDS = [534616491, 987654321]
EVENT_DETAILS = range(1)


async def event_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        event_details = update.message.text
        event_text, event_image = event_details.split('\n')
        event_id = str(uuid.uuid4())  # Generate a unique event ID
        add_event(event_id, event_text, event_image)
        await update.message.reply_photo(photo=event_image, caption=event_text)
        return ConversationHandler.END


async def change_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id in ADMIN_IDS:
        pass
        # Here you should send a form to the admin user to input the new event details
        # After the admin user inputs the new event details, call the change_event function to change the event
        # Then, send a preview of the changed event to the admin user


async def delete_event_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id in ADMIN_IDS:
        pass
        # Here you should ask the admin user to confirm the deletion
        # If the admin user confirms the deletion, call the delete_event function to delete the event
        # Then, send a message to the admin user confirming that the event has been deleted

# Add the command handler and callback query handlers to the dispatcher
