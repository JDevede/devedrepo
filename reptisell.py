from telegram.ext import Updater, CommandHandler

# Define a function to handle the /start command
def start(update, context):
    context.bot.send_message(chat_id=update.message.chat_id, text="Hi!")

def main():

    updater = Updater('6758061728:AAH52BNG1PnFKfxU3_mGsmM5Ro0j3uQXv0A', use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
