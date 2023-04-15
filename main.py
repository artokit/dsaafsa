import asyncio
import subprocess
import threading
import types
from aiogram import Dispatcher, Bot, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
import custom_states
from aiogram import filters, types
import downloader
from business_logic import DB
from pyrogram import Client
import settings
import nest_asyncio
nest_asyncio.apply()

with open('start.txt', 'rb') as f:
    start_text = f.read().decode('utf8')

client = Client('anon', settings.PyrogramSettings.API_ID, settings.PyrogramSettings.API_HASH)
client.start()
bot = Bot(token=settings.AiogramSettings.TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
db = DB()
PRICE = types.LabeledPrice('Подписка', amount=9900)
START_SERVICE = types.InlineKeyboardMarkup(row_width=1).add(
    types.InlineKeyboardButton('Youtube 🍿', callback_data='download:youtube'),
    types.InlineKeyboardButton('VK 👨🏻‍💻', callback_data='download:vk'),
    types.InlineKeyboardButton('Instagram ❤️', callback_data='download:instagram'),
)

DOWNLOAD_TEXT = {
    'youtube': 'пришлите ссылку на материал ⤵️',
    'vk': 'пришлите ссылку на материал ⤵️',
    'instagram': 'пришлите ссылку на материал ⤵️'
}


@dp.message_handler(filters.Command('start'))
async def start(message: types.Message):
    db.add_user(message.chat.id)
    username = message.from_user.username or 'аноним'
    await message.answer(
        start_text.replace('$name', username),
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(text='Продолжить', callback_data='next')
        )
    )


@dp.callback_query_handler(lambda call: call.data == 'next')
async def check_sub(call: types.CallbackQuery):
    user = db.get_user(call.message.chat.id)
    if user.subscribe:
        await call.message.answer(
            'Откуда хотим скачать ?',
            reply_markup=START_SERVICE
        )
    else:
        await bot.send_invoice(
            call.message.chat.id,
            title='Оплата тарифа',
            description='Оплата тарифа',
            provider_token=settings.AiogramSettings.PAYMENT_TOKEN,
            currency='rub',
            is_flexible=False,
            prices=[PRICE],
            start_parameter='time-machine-example',
            payload='some-invoice-payload-for-our-internal-use',
        )


@dp.message_handler(content_types=types.ContentType.SUCCESSFUL_PAYMENT)
async def process_successful_payment(message: types.Message):
    db.set_subscribe(message.chat.id)
    await bot.send_message(
        message.chat.id,
        'Отлично, теперь вы можете пользоваться нашим сервисом',
        reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton('Начать 🚀', callback_data='start'))
    )


@dp.callback_query_handler(lambda call: call.data == 'start')
async def start_service(call: types.CallbackQuery):
    await call.message.answer(
        'Откуда хотим скачать ?',
        reply_markup=START_SERVICE
    )


@dp.message_handler(commands=['vk', 'instagram', 'youtube'])
async def set_service_state(message: types.Message, state: FSMContext):
    await state.set_state(custom_states.EnterLink.enter_link)
    service = message.text.replace('/', '')
    await state.update_data(service=service)
    await message.answer(DOWNLOAD_TEXT[service])


@dp.callback_query_handler(lambda call: call.data.startswith('download'))
async def download_text(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(custom_states.EnterLink.enter_link)
    service = call.data.split(':')[1]
    await state.update_data(service=service)
    await call.message.answer(DOWNLOAD_TEXT[service])


@dp.pre_checkout_query_handler()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message_handler(state=custom_states.EnterLink.enter_link)
async def download(message: types.Message, state: FSMContext):
    service = (await state.get_data())['service']
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(manage_script(service, message)), ]
    loop.run_until_complete(asyncio.wait(tasks))
    # t = threading.Thread(target=manage_script, args=(service, message))
    # t.start()
    # if service == 'youtube':
    #     d = await message.answer('Загружаем видео ⏳')
    #     info = downloader.YouTubeDownloader.download(message.text)
    #     await bot.edit_message_text('Отправляем видео ⏳', d.chat.id, d.message_id)
    #     res = (await client.send_video('@DIIIIIIIIIIIMAbot', open(info.attachments[0], 'rb'))).video
    #     await bot.send_video(message.chat.id, res.file_id)
    #     await bot.delete_message(d.chat.id, d.message_id)
    # if service == 'vk':
    #     info = downloader.VkDownloader.download(message.text)
    #     if len(info.attachments) >= 2:
    #         media_group = types.MediaGroup()
    #         for attachment in info.attachments:
    #             if attachment.type_attachment == downloader.TypeAttachment.PHOTO:
    #                 media_group.attach_photo(types.InputFile(attachment.file_name))
    #             if attachment.type_attachment == downloader.TypeAttachment.VIDEO:
    #                 media_group.attach_video(types.InputFile(attachment.file_name))
    #         await message.answer(info.description, parse_mode='Markdown')
    #         await bot.send_media_group(message.chat.id, media_group)
    #
    #     elif len(info.attachments) == 1:
    #         attachment = info.attachments[0]
    #         if attachment.type_attachment == downloader.TypeAttachment.PHOTO:
    #             await bot.send_photo(message.chat.id, open(attachment.file_name, 'rb'), caption=info.description,
    #                                  parse_mode='Markdown')
    #         if attachment.type_attachment == downloader.TypeAttachment.VIDEO:
    #             await bot.send_video(message.chat.id, open(attachment.file_name, 'rb'), caption=info.description,
    #                                  parse_mode='Markdown')
    #
    #     else:
    #         await message.answer(info.description, parse_mode='Markdown')
    #
    # if service == 'instagram':
    #     attachments, desc = downloader.InstDownloader.download(message.text)
    #     if len(attachments) >= 2:
    #         media_group = types.MediaGroup()
    #         for attachment in attachments:
    #             if attachment.endswith('.jpg') or attachment.endswith('.png'):
    #                 media_group.attach_photo(types.InputFile(attachment))
    #             if attachment.endswith('.mp4') or attachment.endswith('.avi'):
    #                 media_group.attach_video(types.InputFile(attachment))
    #         await message.answer(desc, parse_mode='Markdown')
    #         await bot.send_media_group(message.chat.id, media_group)
    #
    #     elif len(attachments) == 1:
    #         attachment = attachments[0]
    #         if str(attachment).endswith('.jpg') or str(attachment).endswith('.png'):
    #             await bot.send_photo(message.chat.id, open(attachment, 'rb'), caption=desc,
    #                                  parse_mode='Markdown')
    #         if str(attachment).endswith('.mp4') or str(attachment).endswith('.avi'):
    #             await bot.send_video(message.chat.id, open(attachment, 'rb'), caption=desc,
    #                                  parse_mode='Markdown')
    await state.finish()
    # await message.answer('Всё прошло успешно! Что скачаем дальше?', reply_markup=START_SERVICE)


async def manage_script(service, message):
    subprocess.Popen(f'python3 script.py {service} {message.chat.id} {message.text}', shell=True)


executor.start_polling(dp)
