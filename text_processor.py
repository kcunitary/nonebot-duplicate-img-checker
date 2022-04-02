
from .config import gloabal_conf
from datetime import datetime
from asyncio import gather
from .util import mk2Str, fromTimeStamp
from .models import message_type_text
from nonebot.log import logger
import time
#from sqlalchemy import sql as alsql
from Levenshtein import ratio
conf = gloabal_conf


def callout_msg(count, nickname_reply, nickname_last, ltime):
    timeStr = mk2Str(ltime)
    if count > conf["maxCallout"]:
        return None
    now = int(time.time())
    diff = now - ltime
    if diff < conf["cooldown"]*60:
        return None
    msg = f"火星消息警察,对{nickname_reply} 出警! 这条消息由{nickname_last} 在{timeStr} 发过了!"
    if count > 0:
        msg = msg + f"这条消息已经发了{count}次!"
    return msg


def text_data(event):
    query = message_type_text.insert()
    text = event.message.extract_plain_text()
    msg = event.get_message()
    msg_json = [x.__dict__ for x in event.get_message()]
    displayname = ""
    if event.sender.card:
        displayname = event.sender.card
    else:
        displayname = event.sender.nickname
    values = {
        "plain_text": text,
        "message": msg_json,
        "count": 0,
        "text_length": len(text),
        "time": event.time,
        "user_id": event.user_id,
        "user_displayname": displayname,
        "group_id": event.group_id,
        "message_id": event.message_id
    }

    return {
        "query": query,
        "values": values
    }


async def similarTextSearch(db, gid, text):
    # generate sql
    lenConf = conf["minTextLength"]
    if len(text) < lenConf:
        return None

    fullSql = f"""SELECT
	*,
	MATCH ( `plain_text` ) AGAINST ( ":text" ) AS MATCHVALUE 
FROM
	message_type_text 
	
	where group_id = :g_id and text_length > {lenConf}
HAVING
	MATCHVALUE > 80
	ORDER BY MATCHVALUE  desc,id desc"""

#    fullSql = query + lengthFilter + mathquery

    values = {"g_id": gid, "text": text}
    r = await db.fetch_one(query=fullSql, values=values)
    logger.debug(f"text searcher db:{r}")
    if r:
        similarScore = ratio(text, r.plain_text)
        logger.debug(f"similarScore:{similarScore}")
        if similarScore > 0.9:
            return r


async def processText(event,  matcher, db):
    qv = text_data(event)

    text_search_result = await similarTextSearch(db, event.group_id,  qv["values"]["plain_text"])

    tasks = []

    count = 0
    if text_search_result:
        # update count
        count = text_search_result.count + 1
        qv["values"]["count"] = count

        # msg

        msg = callout_msg(count, event.sender.nickname,
                          text_search_result.user_displayname, text_search_result.time)
        if msg:
            tasks.append(matcher.send(msg))

    tasks.append(db.execute(**qv))
    r = await gather(*tasks)
    return r
