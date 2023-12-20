from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# Define a function to handle the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! I'm your bot.")

def main():
    # Token for the bot
    TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'

    # Create an updater object
    updater = Updater(token=TOKEN, use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register a handler for the /start command
    dp.add_handler(CommandHandler("start", start))

    # Register a handler for messages
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
