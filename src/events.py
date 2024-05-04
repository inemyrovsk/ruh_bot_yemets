from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import ContextTypes
import sqlite3
from database import register_user_to_event

ADMIN_IDS = [534616491, 987654321]

async def show_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Fetch events from the database
    events = fetch_all_events()  # This function should return a list of event dictionaries
    if not events:
        await update.message.reply_text("No events found.")
        return

    # Store events in context to use in navigation
    context.user_data['events'] = events
    context.user_data['current_event_index'] = 0

    # Send the first event
    await send_event(update, context)


def fetch_all_events():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute("SELECT * FROM Events")
    events = c.fetchall()

    conn.close()

    # Convert the events to a list of dictionaries
    events = [{"id": str(id), "text": name, "image_path": image, "time": time, "location": location} for id, name, image, date, time, location in events]

    return events


async def send_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = context.user_data['events']
    index = context.user_data['current_event_index']
    event = events[index]
    event_id = event['id']

    # Create navigation buttons
    navigation_buttons = [
        InlineKeyboardButton("⬅️ Previous", callback_data="previous_event"),
        InlineKeyboardButton(f"{index + 1} / {len(events)}", callback_data="event"),
        InlineKeyboardButton("Next ➡️", callback_data="next_event")
    ]

    action_buttons = [
        InlineKeyboardButton("Приєднатися", callback_data=f"join_{event_id}")
    ]

    admin_buttons = []
    if update.effective_user.id in ADMIN_IDS:
        admin_buttons = [
            [InlineKeyboardButton("Change Event", callback_data=f"change_event_{event_id}")],
            [InlineKeyboardButton("Delete Event", callback_data=f"delete_event_{event_id}")]
        ]

    reply_markup = InlineKeyboardMarkup([navigation_buttons, action_buttons] + admin_buttons)

    # Create the message text with event details
    message_text = f"{event['text']}\nTime: {event['time']}\nLocation: {event['location']}"

    # Send or edit the message with the event
    if update.callback_query:
        await update.callback_query.answer()
        if event['image_path']:  # Check if there is an image to send
            await update.callback_query.edit_message_media(
                media=InputMediaPhoto(open(event['image_path'], 'rb'), caption=message_text),
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.edit_message_text(
                text=message_text,
                reply_markup=reply_markup
            )
    else:
        if event['image_path']:  # Check if there is an image to send
            await update.message.reply_photo(
                photo=open(event['image_path'], 'rb'),
                caption=message_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                text=message_text,
                reply_markup=reply_markup
            )


async def navigate_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    events = context.user_data['events']
    index = context.user_data['current_event_index']

    if data == 'next_event' and index < len(events) - 1:
        context.user_data['current_event_index'] += 1
    elif data == 'previous_event' and index > 0:
        context.user_data['current_event_index'] -= 1

    await send_event(update, context)


async def register_button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = query.data.split('_')[1]  # Extract the event ID from the callback query
    user_id = update.effective_user.id

    # Function to add user to the event in the database
    is_registered = register_user_to_event(user_id, event_id)

    if is_registered:
        await query.answer("You have been registered for the event!")
        await query.edit_message_caption(caption=f"{query.message.caption}\n\nRegistered!")
    else:
        await query.answer("You are already registered for the event!")
