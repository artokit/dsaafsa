import os
import random
import sys
import asyncio
from aiogram import Bot, types
import settings
import downloader
from pyrogram import Client
bot = Bot(token=settings.AiogramSettings.TOKEN)
letters = '1234567890qwertyuiopasdfghjklzxcvbnm'
temp_name = ''.join(random.choices(list(set(list(letters) + list(letters.upper()))), k=16))
w = open(f'{temp_name}.session', 'wb')
f = open('anon.session', 'rb')
w.write(f.read())
f.close()
w.close()
client = Client(f'{temp_name}', settings.PyrogramSettings.API_ID, settings.PyrogramSettings.API_HASH)
client.start()
DOG_BOT = '@iSave_by_bot'


async def manage(service, chat_id, link):
    d = await bot.send_message(chat_id, 'Загружаем данные ⏳')

    if service == 'youtube':
        info = downloader.YouTubeDownloader.download(link)
        await bot.edit_message_text('Отправляем видео ⏳', d.chat.id, d.message_id)
        file = open(info.attachments[0], 'rb')
        res = (await client.send_video(DOG_BOT, file)).video
        file.close()
        os.remove(info.attachments[0])
        await bot.send_video(chat_id, res.file_id)
        await bot.delete_message(d.chat.id, d.message_id)

    if service == 'vk':
        info = downloader.VkDownloader.download(link)
        await bot.edit_message_text('Отправляем данные ⏳', d.chat.id, d.message_id)
        if len(info.attachments) >= 2:
            media_group = types.MediaGroup()
            for attachment in info.attachments:
                if attachment.type_attachment == downloader.TypeAttachment.PHOTO:
                    media_group.attach_photo(types.InputFile(attachment.file_name))
                if attachment.type_attachment == downloader.TypeAttachment.VIDEO:
                    file = open(attachment.file_name, 'rb')
                    res = (await client.send_video(DOG_BOT, file)).video
                    file.close()
                    media_group.attach_video(res.file_id)
            if info.description:
                await bot.send_message(chat_id, info.description, parse_mode='Markdown')
            await bot.send_media_group(chat_id, media_group)

        elif len(info.attachments) == 1:
            attachment = info.attachments[0]
            if attachment.type_attachment == downloader.TypeAttachment.PHOTO:
                await bot.send_photo(chat_id, open(attachment.file_name, 'rb'), caption=info.description,
                                     parse_mode='Markdown')
            if attachment.type_attachment == downloader.TypeAttachment.VIDEO:
                file = open(attachment.file_name, 'rb')
                res = (await client.send_video(DOG_BOT, file)).video
                file.close()
                await bot.send_video(chat_id, res.file_id, caption=info.description,
                                     parse_mode='Markdown')

        else:
            await bot.send_message(chat_id, info.description, parse_mode='Markdown')

        for attachment in info.attachments:
            os.remove(attachment.file_name)

        await bot.delete_message(d.chat.id, d.message_id)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    tasks = [loop.create_task(manage(*sys.argv[1:])), ]
    loop.run_until_complete(asyncio.wait(tasks))
    try:
        os.remove(f'{temp_name}.session')
        os.remove(f'{temp_name}.session-journal')
    except FileNotFoundError:
        pass
