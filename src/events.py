import os
import csv
import main
import sqlite3
from telegram.ext import ContextTypes
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto, InputFile
from database import register_user_to_event, fetch_users_by_event_id

ADMIN_IDS = [int(id.strip()) for id in os.environ["ADMIN_IDS"].split(',')]

# [534616491]


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
    events = [{"id": str(id), "text": name, "image_path": image, "time": time, "location": location} for
              id, name, image, date, time, location in events]

    return events


async def send_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    events = context.user_data['events']
    index = context.user_data['current_event_index']
    event = events[index]
    event_id = event['id']
    print(event_id)

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
            [InlineKeyboardButton("Delete Event", callback_data=f"delete_event_{event_id}")],
            [InlineKeyboardButton("Show Registered Users", callback_data=f"show_joined_{event_id}")]
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


async def change_event_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = query.data.split('_')[2]  # Extract the event ID from the callback query

    # Fetch event details from the database
    event = fetch_event_by_id(event_id)

    if event:
        context.user_data['event_to_modify'] = event

        reply_markup = main.change_event_buttons(event_id)

        # Send a new message with the event details to modify
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"Choose what to change for event '{event['text']}':",
            reply_markup=reply_markup
        )
    else:
        await query.answer("Event not found.")


async def change_event_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    detail_type, event_id = query.data.split('_')[1:3]

    print(f"Handling change for {detail_type} with event ID {event_id}")  # Log for debugging

    context.user_data['event_detail_type'] = detail_type
    context.user_data['event_id_to_change'] = event_id

    await query.edit_message_text(
        text=f"Enter the new {detail_type} for the event:"
    )

async def receive_new_event_details(update: Update, context: ContextTypes.DEFAULT_TYPE):
    detail_type = context.user_data.get('event_detail_type')
    event_id = context.user_data.get('event_id_to_change')
    updated_event = fetch_event_by_id(event_id)

    print("Received new event details", detail_type, event_id)
    if detail_type == 'image':
        photo = update.message.photo[-1]
        print(photo)
        file = await context.bot.get_file(photo.file_id)
        local_image_path = os.path.join('images', f"{file.file_id}.jpg")
        await file.download_to_drive(custom_path=local_image_path)
        new_detail = local_image_path
        updated_event["image_path"] = new_detail
    elif detail_type == 'name':
        updated_event['text'] = update.message.text
        new_detail = update.message.text
    else:
        updated_event[detail_type] = update.message.text
        new_detail = update.message.text

    context.user_data['detail_type'] = detail_type
    context.user_data['new_detail'] = new_detail

    reply_markup = main.change_event_buttons(event_id)

    # Send a new message with a preview of the updated event and an approval button
    await update.message.reply_photo(
        photo=updated_event['image_path'],
        caption=f"{updated_event['text']}\nTime: {updated_event['time']}\nLocation: {updated_event['location']}",
        reply_markup=reply_markup
    )



async def approve_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = context.user_data.get('event_id_to_change')  # Extract the event ID from the callback query
    detail_type = context.user_data.get('detail_type')
    new_detail = context.user_data.get('new_detail')
    # Finalize the changes to the event in the database
    if update_event_details(event_id, detail_type, new_detail):
        updated_event = fetch_event_by_id(event_id)
        await update.callback_query.message.reply_photo(
            photo=updated_event['image_path'],
            caption=f"{updated_event['text']}\nTime: {updated_event['time']}\nLocation: {updated_event['location']}",
            reply_markup=main.main_buttons(admin=True)
        )
    else:
        await query.answer("Failed to approve event changes.")


def fetch_event_by_id(event_id):
    conn = sqlite3.connect('database.db')
    try:
        c = conn.cursor()
        c.execute("SELECT id, name, image, time, location FROM Events WHERE id=?", (event_id,))
        event_row = c.fetchone()
        print('Fetched event row:', event_row)  # Log the result to debug

        if event_row:
            return {"id": str(event_row[0]), "text": event_row[1], "image_path": event_row[2], "time": event_row[3], "location": event_row[4]}
    except Exception as e:
        print(f"Error fetching event by ID {event_id}: {e}")  # Log any errors
    finally:
        conn.close()
    return None


def update_event_details(event_id, detail_type, new_detail):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    if detail_type == "name":
        c.execute("UPDATE Events SET name=? WHERE id=?", (new_detail, event_id))
    elif detail_type == "time":
        c.execute("UPDATE Events SET time=? WHERE id=?", (new_detail, event_id))
    elif detail_type == "image":
        print("Updating image", new_detail)
        c.execute("SELECT image FROM Events WHERE id=?", (event_id,))
        result = c.fetchone()
        print("Previous image", result)
        if result is not None:
            image_path = result[0]
            # Delete previous image from local storage
            print("Deleting previous image", image_path)
            if os.path.isfile(image_path):
                os.remove(image_path)

        c.execute("UPDATE Events SET image=? WHERE id=?", (new_detail, event_id))
        print("Updated image", new_detail)
    elif detail_type == "location":
        c.execute("UPDATE Events SET location=? WHERE id=?", (new_detail, event_id))
    conn.commit()
    conn.close()
    return True

async def show_joined_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = query.data.split('_')[2]  # Extract the event ID from the callback query

    # Fetch event details from the database
    event = fetch_event_by_id(event_id)

    if event:
        context.user_data['event_to_show_users'] = event

        # Fetch the users joined the event from the database
        users = fetch_users_by_event_id(event_id)  # This function should return a list of user dictionaries

        # Write the users into a CSV file
        with open(f'guests-{event_id}.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["User ID", "Name", "Phone Number"])  # Header
            for user in users:
                writer.writerow([user['user_id'], user['name'], user['phone_number']])

        # Send the CSV file
        with open(f'guests-{event_id}.csv', 'rb') as file:
            await context.bot.send_document(chat_id=query.message.chat_id, document=InputFile(file))

    else:
        await query.answer("Event not found.")


async def delete_event_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    event_id = query.data.split('_')[2]  # Extract the event ID from the callback query

    # Delete the event from the database
    delete_event(event_id)

    # Send a confirmation message
    await query.answer("Event deleted.")

def delete_event(event_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('DELETE FROM Events WHERE id = ?', (event_id,))
    c.execute('DELETE FROM EventParticipants WHERE event_id = ?', (event_id,))

    conn.commit()
    conn.close()