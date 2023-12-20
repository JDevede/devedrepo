import logging
import ssl

from aiogram import Bot, filters, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import Dispatcher, FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.webhook import get_new_configured_app
from aiogram.types import ContentTypes, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
from aiohttp import web


class States(StatesGroup):
    category = State()
    species = State()
    wc = State()
    gender = State()
    year = State()
    morph = State()
    place = State()
    price = State()
    photo = State()

banned = []
def init_banned(b: list) -> None:
    with open("banned.txt") as f:
        for user in f:
            u = user.strip()
            if u.lower() != "":
                logging.info(f"User banned: {user}")
                b.append(u.lower())
        logging.info(f"Total: {banned}")

n_file = 0
admins_chat_ids = {}
images = {}

TOKEN = "1152535571:AAGcPW2wHIHlVKPIXS9xlK-4DwusqiDXJjs"
# webhook settings
WEBHOOK_HOST = "165.22.119.67"
WEBHOOK_PATH = "/{TOKEN}"
WEBHOOK_PORT = 80
WEBHOOK_URL = f"https://{WEBHOOK_HOST}:{WEBHOOK_PORT}{WEBHOOK_PATH}"
WEBHOOK_SSL_CERT = "./webhook_cert.pem"  # Path to the ssl certificate
WEBHOOK_SSL_PRIV = "./webhook_pkey.pem"  # Path to the ssl private key

# webserver settings
WEBAPP_HOST = WEBHOOK_HOST
WEBAPP_PORT = WEBHOOK_PORT

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
channel_id = "@reptisell"


def get_message_caption(data, username):
    return f"""Reptile from {username}
Category: {data['category']}
Species: {data['species']}
WC: {data['wc']}
Gender: {data['gender']}
Age: {data['year']}
Morph: {data['morph']}
Location: {data['place']}
Price: {data['price']}"""


def gen_kb(data, factory):
    kb = InlineKeyboardMarkup()
    for index, text in enumerate(data):
        kb.insert(InlineKeyboardButton(text, callback_data=factory.new(index=index)))
    return kb

CATEGORIES = ["Sauri", "Serpenti", "Testuggini", "Anfibi", "Aracnidi", "Insetti"]
WC = ["WC", "CB"]
GENDER = ["Maschio(1.0)", "Femmina (0.1)", "Non Sessato (0.0.1)"]
APPROVAL = ["👎", "👍"]
category_f = CallbackData("category", "index", sep="_")
wc_f = CallbackData("wc", "index", sep="_")
gender_f = CallbackData("gender", "index", sep="_")
approval_f = CallbackData("approval", "decision", "chat_id", "file_id", sep="SEPARA")
category_kb = gen_kb(CATEGORIES, category_f)
wc_kb = gen_kb(WC, wc_f)
gender_kb = gen_kb(GENDER, gender_f)

def get_approval_kb(chat_id, file_id, descr):
    logging.info(f"chat: {chat_id}\nfile: {file_id}")
    approval_kb = InlineKeyboardMarkup()
    for index, text in enumerate(APPROVAL):
        approval_kb.insert(
            InlineKeyboardButton(
                text,
                callback_data=approval_f.new(
                    decision = index,
                    chat_id = chat_id,
                    file_id = file_id,
                )
            )
        )
    return approval_kb

@dp.message_handler(commands=["start"])
# @dp.throttled(lambda msg, loop, *args, **kwargs: loop.create_task(bot.send_message(msg.from_user.id, "Puoi inserire un annuncio ogni 12 minuti, sei pregato di aspettare.")), rate=720)
async def handle_start(message: types.Message):
    logging.info(f"Start from {message.from_user.username}")
    not_none = message.from_user.username is not None
    if not_none and ("@" + message.from_user.username not in banned):
        await States.category.set()
        await message.reply(
            """Benvenuto su ReptiSell, il primo bot dedicato alla terraristica.
    Qui potrai inserire il tuo annuncio rispondendo a poche semplici domande.
    Troverai tutti gli annunci sul canale @ReptiSell.
    Per iniziare digita /start.

    Non ci assumiamo nessuna responsabilità per la trasgressione delle leggi riguardanti il paese a cui si riferisce ogni utente che pubblica il proprio annuncio o sulle condizioni di gestione ma ci impegneremo a segnalarli.
    Per segnalazioni contattate @OmarAmerio"""
        )
        await message.reply("CATEGORIA:", reply_markup=category_kb)
    else:
        await message.reply("Sei stato bannato! :c")


@dp.callback_query_handler(category_f.filter(), state=States.category)
async def process_category(
        query: types.CallbackQuery, state: FSMContext, callback_data: dict
):
    index = int(callback_data["index"])
    category = CATEGORIES[index]
    async with state.proxy() as data:
        data["category"] = category
    await States.next()
    await query.message.edit_text(f"Hai scelto: {category}")
    await query.message.reply("INDICA LA SPECIE ( NOME SCIENTIFICO)", reply=False)


@dp.message_handler(state=States.species)
async def process_species(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["species"] = message.text
    await States.next()
    await message.reply(
        "WC (CATTURATO IN NATURA) / CB (NATO IN CATTIVITA’)", reply_markup=wc_kb
    )


@dp.callback_query_handler(wc_f.filter(), state=States.wc)
async def process_wc(
        query: types.CallbackQuery, state: FSMContext, callback_data: dict
):
    index = int(callback_data["index"])
    wc = WC[index]
    async with state.proxy() as data:
        data["wc"] = wc
    await States.next()
    await query.message.edit_text(f"Hai scelto: {wc}")
    await query.message.reply(
        "Maschio(1.0) Femmina (0.1) Non Sessato (0.0.1)",
        reply=False,
        reply_markup=gender_kb,
    )


@dp.callback_query_handler(gender_f.filter(), state=States.gender)
async def process_gender(
        query: types.CallbackQuery, state: FSMContext, callback_data: dict
):
    index = int(callback_data["index"])
    gender = GENDER[index]
    async with state.proxy() as data:
        data["gender"] = gender
    await States.next()
    await query.message.edit_text(f"Hai scelto: {gender}")
    await query.message.reply("Anno", reply=False)


@dp.message_handler(state=States.year)
async def process_year(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["year"] = message.text
    await States.next()
    await message.reply("MORPH")


@dp.message_handler(state=States.morph)
async def process_morph(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["morph"] = message.text
    await States.next()
    await message.reply("DOVE SI TROVA IL RETTILE?")


@dp.message_handler(state=States.place)
async def process_place(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["place"] = message.text
    await States.next()
    await message.reply("PREZZO")


@dp.message_handler(state=States.price)
async def process_price(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data["price"] = message.text
    await States.next()
    await message.reply("INVIA UNA FOTO DELL’ANIMALE")


@dp.message_handler(state=States.photo, content_types=ContentTypes.PHOTO)
async def process_photo(message: types.Message, state: FSMContext):
    global n_file
    async with state.proxy() as data:
        data["photo"] = message.photo[-1]
        username = message.from_user.get_mention()
        await message.reply(
            "Perfetto, dopo l'approvazione potrai trovare il tuo annuncio su @ReptiSell.\n\nPer inserire un altro annuncio digita /start"
        )
        logging.info("Picture from " + message.from_user.username)
        logging.info(f"Username: {username}\ndata: {data}")
        logging.info("Caption: " + get_message_caption(data, username))
        logging.info(f"Chat id: {message.chat.id}")
        images[n_file] = {"id": data['photo'].file_id, "desc": get_message_caption(data, username)}
        n_file += 1
        await bot.send_photo(
            int("-1001319647910"),
            data["photo"].file_id,
            caption=get_message_caption(data, username),
            parse_mode="markdown",
            reply_markup=get_approval_kb(
                message.chat.id,
                n_file - 1,
                get_message_caption(data, username)
            )
        )
    await state.finish()
@dp.message_handler(commands=["ping"])
async def ping(message: types.Message):
    await bot.send_message(message.chat.id, "pong")

@dp.message_handler(commands = ["ban"])
async def ban(message: types.Message):
    if message.from_user.id in admins_chat_ids:
        logging.info(message.text)
        to_ban = message.text.split(" ")[1:]
        logging.info(f"To ban: {to_ban}")
        banned.extend(to_ban)
        with open("banned.txt", "w") as f:
            for u in banned:
                f.write(u + "\n")
        msg = "Utente/i bannato/i!\nUtenti attualmente bannati:\n"
        for b in banned:
            msg += (b + "\n")
        await bot.send_message(message.chat.id, msg)
    else:
        await bot.send_message(message.chat.id, "Non hai i permessi per usare questo comando! :c")
@dp.message_handler(commands = ["list"])
async def list_ban(message: types.Message):
    msg = "Utenti bannati:\n"
    for u in banned:
        msg += (u + "\n")
    msg += f"Totale: {len(banned)}"
    await bot.send_message(
        message.chat.id,
        msg
    )
@dp.message_handler(commands = ["unban"])
async def unban(message: types.Message):
    if message.from_user.id in admins_chat_ids:
        logging.info(message.text)
        to_unban = message.text.split(" ")[1:]
        logging.info(to_unban)
        for user in to_unban:
            if user.lower() in banned:
                banned.remove(user.lower())
        with open("banned.txt", "w") as f:
            for u in banned:
                f.write(u.strip() + "\n")
        msg = "Utente/i sbannato/i! Utenti attualmente bannati: \n"
        for b in banned:
            msg += (b + "\n")
        await bot.send_message(message.chat.id, msg)
    else:
        await bot.send_message(message.chat.id, "Non hai i permessi per usare questo comando! :c")

@dp.message_handler(commands=["verify"])
async def verify(message: types.Message):
    admins_chat_ids[message.from_user.id] = message.chat.id
    await bot.send_message(message.chat.id, "Sei stato registrato come admin!")

@dp.callback_query_handler(approval_f.filter())
async def decide(query: types.CallbackQuery, callback_data: dict):
    yes = bool(int(callback_data['decision']))
    index = int(callback_data['file_id'])
    logging.info(f"cb_data: {callback_data}")
    logging.info(f"images: {images}")
    logging.info(f"current image: {images[index]}")
    if yes:
        if index in images:
            await bot.send_photo(
                channel_id,
                images[index]["id"],
                caption = images[index]["desc"],
                parse_mode = "markdown"
            )
        del images[index]
    else:
        await bot.send_message(
            callback_data["chat_id"],
            "L'annuncio non è stato approvato :c"
        )


async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL, certificate=open(WEBHOOK_SSL_CERT, "rb"))


async def on_shutdown(dp):
    logging.warning("Shutting down..")
    await bot.delete_webhook()
    logging.warning("Bye!")


if __name__ == "__main__":
    app = get_new_configured_app(dispatcher=dp, path=WEBHOOK_PATH)
    init_banned(banned)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
    context.load_cert_chain(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV)
    web.run_app(app, host=WEBAPP_HOST, port=WEBAPP_PORT, ssl_context=context)
