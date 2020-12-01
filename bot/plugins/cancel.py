from pyrogram import filters as Filters

from ..utubebot import UtubeBot


@UtubeBot.on_callback_query(Filters.create(lambda _, __, query: query.data.startswith('cncl+')))
async def cncl(c, q):
    _, pid = q.data.split('+')
    if not c.download_controller.get(pid, False):
        await q.answer("عمليتك غير نشطة", show_alert=True)
        return
    c.download_controller[pid] = False
    await q.answer("سيتم إلغاء عمليةك قريبا!", show_alert=True)
