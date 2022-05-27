from .models import group_message_sender, message_type_text, message_type_pic, group_message_meta
from nonebot.plugin import require
from nonebot import on_message
from asyncio import gather
from .text_processor import text_process
from .pic_processor import pics_process
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.plugin import export
# .event
# init db
dbexport = require("nonebot_plugin_navicat")
db = dbexport.mysql_pool

export=export()
export.group_message_sender = group_message_sender
export.message_type_text = message_type_text
export.message_type_pic = message_type_pic
export.group_message_meta = group_message_meta

async def msg_metadata_insert(db, event: GroupMessageEvent):
    query = group_message_meta.insert()
    values = {
        "time": event.time,
        "self_id": event.self_id,
        "sub_type": event.sub_type,
        "user_id": event.user_id,
        "message_type": event.message_type,
        "message_id": event.message_id,
        "font": event.font,
        "to_me": event.to_me,
        "group_id": event.group_id
    }
    return await db.execute(query=query, values=values)


async def msg_sender_data_insert(db, event: GroupMessageEvent):
    sender = event.sender
    query = group_message_sender.insert()
    values = {
        "user_id": sender.user_id,
        "nickname": sender.nickname,
        "sex": sender.sex,
        "age": sender.age,
        "card": sender.card,
        "area": sender.area,
        "level": sender.level,
        "role": sender.role,
        "title": sender.title,
        "time": event.time,
        "group_id": event.group_id
    }
    return await db.execute(query=query, values=values)


any_msg = on_message(priority=99, block=False)


@any_msg.handle()
async def handle(event: GroupMessageEvent):

    tasks = [
        msg_metadata_insert(db, event),
        msg_sender_data_insert(db, event),
        text_process(event, any_msg, db),
        pics_process(event, any_msg, db)
    ]
    r = await gather(
        *tasks
    )
