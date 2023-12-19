from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext

# Define a function to handle the /start command
def start(update: Update, context: CallbackContext) -> None:
    user = update.message.from_user
    update.message.reply_text(f"Hello, {user.first_name}!")

def main() -> None:
    # Create the Updater and pass in your bot's token
    updater = Updater("6758061728:AAH52BNG1PnFKfxU3_mGsmM5Ro0j3uQXv0A", use_context=True)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # Register a command handler for the /start command
    dp.add_handler(CommandHandler("start", start))

    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
