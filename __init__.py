from .models import group_message_sender, message_type_text, message_type_pic, group_message_meta
from nonebot.plugin import require
from nonebot import on_message, on_command
from nonebot.adapters.cqhttp import GroupMessageEvent
from nonebot.log import logger
from asyncio import gather
from .text_processor import processText
from .pic_processor import pics_process


# init db
export = require("nonebot_plugin_navicat")
db = export.mysql_pool

def main_meata(event):
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
    return {
        "query": query,
        "values": values
    }


def sender_data(event):
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
    return {
        "query": query,
        "values": values
    }


any_msg = on_message(priority=99, block=False
                     )


@any_msg.handle()
async def handle(bot, event: GroupMessageEvent, state):
    # insert main
    main_meata_query = main_meata(event)
    logger.debug(
        "main_meata_query:", main_meata_query
    )

    sender_query = sender_data(event)
    logger.debug(
        f"sender_query:{sender_query}"
    )
    tasklist = [
        db.execute(**main_meata_query),
        db.execute(**sender_query),
        processText(event, any_msg,db),
        pics_process(event, any_msg,db)
    ]
    r = await gather(
        *tasklist
    )
