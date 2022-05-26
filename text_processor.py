
from .config import gloabal_conf
from datetime import datetime
from asyncio import gather
from .util import mk2Str, fromTimeStamp
from .models import message_type_text
from nonebot.log import logger
import time

from Levenshtein import ratio
conf = gloabal_conf

def conf_filter(the_record,last_record):
    if not conf["calloutSelf"]:
        if last_record.user_id == the_record["user_id"]:
            return False
    if conf["cooldown"] > 0:
        timeStr = mk2Str(last_record.time)
        now = int(time.time())
        diff = now - last_record.time
        if (diff < conf["cooldown"]*60):
            return False
    if the_record["count"] > conf["maxCallout"]:
        return False
    return True


def callout_msg(count, nickname_reply, nickname_last, ltime):
    timeStr = mk2Str(ltime)
    if count > conf["maxCallout"]:
        return None
    now = int(time.time())
    diff = now - ltime
    if diff < conf["cooldown"]*60:
        return None
    msg = f"火星消息警察,对{nickname_reply} 出警! 这条消息由{nickname_last} 在{timeStr} 发过了!\r\n"
    msg = msg + f"这条消息已经发了{count} 次!"
    return msg


def msg_text_insert_pre(event):
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
    return values


async def full_text_search(db, gid, text):
    lenConf = conf["minTextLength"]
    text_len = len(text)
    if text_len < lenConf:
        return None
    top_len = int(text_len * 1.1)

    bottom_len = max(int(text_len * 0.9),lenConf)
    time_range = fromTimeStamp()
    fullSql = """SELECT
	*,
	MATCH ( `plain_text` ) AGAINST ( ":text" ) AS MATCHVALUE 
FROM
	message_type_text 
	
	where group_id = :g_id 
    and text_length BETWEEN  :b_len and :t_len
    and time > :time_range
HAVING
	MATCHVALUE > 80
	ORDER BY MATCHVALUE  desc,id desc
LIMIT 1
    """

    values = {"g_id": gid, "text": text,"b_len": bottom_len, "t_len": top_len,"time_range": time_range}

    r = await db.fetch_one(query=fullSql, values=values)
    logger.debug(f"text searcher db:{r}")
    if r:
        similarScore = ratio(text, r.plain_text)
        logger.debug(f"similarScore:{similarScore}")
        if similarScore > 0.9:
            return r


async def text_process(event,  matcher, db):
    tasks = []
    sql_vals = msg_text_insert_pre(event)

    full_text_search_r = await full_text_search(db, event.group_id,event.message.extract_plain_text())

    if full_text_search_r:
        # update count
        r_count  = full_text_search_r.count + 1
        sql_vals["count"] = r_count

        # msg
        msg = callout_msg(r_count, event.sender.nickname,
                          full_text_search_r.user_displayname, 
                          full_text_search_r.time)
        if msg and conf_filter(sql_vals,full_text_search_r):
            tasks.append(matcher.send(msg))
    tasks.append(db.execute(query=message_type_text.insert(),values=sql_vals))
    r = await gather(*tasks)
    return r


