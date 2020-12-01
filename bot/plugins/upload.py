import os
import time
import string
import random
import logging
import asyncio
import datetime

from pyrogram import StopTransmission
from pyrogram import filters as Filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ..translations import Messages as tr
from ..helpers.downloader import Downloader
from ..helpers.uploader import Uploader
from ..config import Config
from ..utubebot import UtubeBot


log = logging.getLogger(__name__)


@UtubeBot.on_message(
    Filters.private 
    & Filters.incoming 
    & Filters.command('upload') 
    & Filters.user(Config.AUTH_USERS)
)
async def _upload(c, m):
    if not os.path.exists(Config.CRED_FILE):
        await m.reply_text(tr.NOT_AUTHENTICATED_MSG, True)
        return

    if not m.reply_to_message:
        await m.reply_text(tr.NOT_A_REPLY_MSG, True)
        return

    message = m.reply_to_message

    if not message.media:
        await m.reply_text(tr.NOT_A_MEDIA_MSG, True)
        return

    if not valid_media(message):
        await m.reply_text(tr.NOT_A_VALID_MEDIA_MSG, True)
        return
    
    if c.counter >= 6:
        await m.reply_text(tr.DAILY_QOUTA_REACHED, True)

    snt = await m.reply_text(tr.PROCESSING, True)
    c.counter += 1
    download_id = get_download_id(c.download_controller)
    c.download_controller[download_id] = True

    download = Downloader(m)
    status, file = await download.start(progress, snt, c, download_id)
    log.debug(status, file)
    c.download_controller.pop(download_id)
    
    if not status:
        c.counter -= 1
        c.counter = max(0, c.counter)
        await snt.edit_text(text = file, parse_mode='markdown')
        return
    
    await snt.edit_text("تم التنزيل جاري الرفع الى يوتيوب")
    title = ' '.join(m.command[1:])
    upload = Uploader(file, title)
    status, link = await upload.start(progress, snt)
    log.debug(status, link)
    if not status:
        c.counter -= 1
        c.counter = max(0, c.counter)
    await snt.edit_text(text = link, parse_mode='markdown')


def get_download_id(storage):
    while True:
        download_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if download_id not in storage:
            break
    return download_id


def valid_media(media):
    if media.video:
        return True
    elif media.video_note:
        return True
    elif media.animation:
        return True
    elif media.document and 'video' in media.document.mime_type:
        return True
    else:
        return False


def human_bytes(num, split=False):
    base = 1024.0
    sufix_list = ['B','KB','MB','GB','TB','PB','EB','ZB', 'YB']
    for unit in sufix_list:
        if abs(num) < base:
            if split:
                return round(num, 2), unit
            return f"{round(num, 2)} {unit}"
        num /= base


async def progress(cur, tot, start_time, status, snt, c, download_id):
    if not c.download_controller.get(download_id):
        raise StopTransmission
        
    try:
        diff = int(time.time()-start_time)
        
        if (int(time.time()) % 5 == 0) or (cur==tot):
            await asyncio.sleep(1)
            speed, unit = human_bytes(cur/diff, True)
            curr = human_bytes(cur)
            tott = human_bytes(tot)
            eta = datetime.timedelta(seconds=int(((tot-cur)/(1024*1024))/speed))
            elapsed = datetime.timedelta(seconds=diff)
            progress = round((cur * 100) / tot, 2)
            text = f"{status}\n\n{progress}% انتهى\n{curr} من {tott}\n بسرعة : {speed} {unit}PS\nETA: {eta}\nانتهى :  {elapsed}"
            await snt.edit_text(
                text = text, 
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton('ايقاف !', f'cncl+{download_id}')
                        ]
                    ]
                )
            )

    except Exception as e:
        log.info(e)
        pass
