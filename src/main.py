from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import handlers
from events import show_events, navigate_event, register_button_callback
from database import initialize_db
from admin_panel import change_event_callback, delete_event_callback


def main():
    application = Application.builder().token('7103471562:AAE-sSu1eWqJ8s5o4-yBl92YJAve-lUZSWs').build()
    application.add_handler(CommandHandler("start", handlers.share_contact))
    application.add_handler(MessageHandler(filters.CONTACT, handlers.contact_handler))
    application.add_handler(MessageHandler(filters.Regex('^Admin$'), handlers.admin_handler))
    application.add_handler(MessageHandler(filters.Regex('^Show all Events'), show_events))
    application.add_handler(CallbackQueryHandler(navigate_event, pattern='^(next_event|previous_event)$'))
    application.add_handler(handlers.conv_handler)
    application.add_handler(CallbackQueryHandler(register_button_callback, pattern='^join_'))

    application.add_handler(CallbackQueryHandler(change_event_callback, pattern='^change_event$'))
    application.add_handler(CallbackQueryHandler(delete_event_callback, pattern='^delete_event$'))

    application.run_polling()


if __name__ == '__main__':
    initialize_db()
    main()
