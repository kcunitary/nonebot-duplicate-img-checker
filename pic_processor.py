from nonebot.log import logger
from .config import gloabal_conf
from sqlalchemy import or_
from asyncio import gather
from functools import partial
from .util import fromTimeStamp, mk2Str

import aiohttp
from io import BytesIO
from PIL import Image
import imagehash
from sqlalchemy import sql as alsql
from .models import message_type_pic, message_type_pic_hash
import time
import sys


from .fastimage.fastimage import detect


conf = gloabal_conf


async def getOCR():
    return {
        "ocr_text": "",
        "ocr_len": ""
    }


async def getSizeFast(url):
    width, height = await detect.get_size(url)
    info = {
        "img_width": width,
        "img_height": height,
    }
    return info


async def getImg_WH_Hash(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            img = Image.open(BytesIO(await resp.read()))
            width, height = img.size
            img_hash = imagehash.dhash(img)
    return {
        "img_width": width,
        "img_height": height,
        "img_hash": str(img_hash)
    }


def hamming_distance_string(a, b):
    ai = int(a, 16)
    bi = int(b, 16)
    bins = bin(ai ^ bi)
    r = bins.count("1")
    return r


async def similar_pic_search(v, db):
    nHash = v["img_hash"]
    pre_TimeStamp = fromTimeStamp()
    hash_list = []
    for i in range(4):
        hash_segment = nHash[i*4:(i+1)*4]
        hash_list.append(hash_segment)

    query = alsql.select(message_type_pic_hash.c.message_id).where(
        message_type_pic_hash.c.group_id == v["group_id"],
        message_type_pic_hash.c.time > pre_TimeStamp,
        message_type_pic_hash.c.img_hash.in_(hash_list)
    ).order_by(
        message_type_pic_hash.c.id.desc()
    )
    r = await db.fetch_one(query=query)
    if r:
        query_raw_pic = alsql.select(message_type_pic).where(
            message_type_pic.c.message_id == r.message_id
        ).order_by(
            message_type_pic.c.id.desc()
        )

        r2 = await db.fetch_one(query=query_raw_pic)
        logger.debug(f"r:{r},r2:{r2}")
        distance = hamming_distance_string(r2.img_hash, nHash)
        if distance < 4:
            return r2
#    return None


def make_pic_baseinfo(msg,  event):
    urlHash = msg.data["file"].split(".")[-2]
    displayname = ""
    if event.sender.card:
        displayname = event.sender.card
    else:
        displayname = event.sender.nickname
    v = {
        "url": msg.data["url"],
        "url_hash": urlHash,
        "count": 0,
        "time": event.time,
        "user_id": event.user_id,
        "user_displayname": displayname,
        "group_id": event.group_id,
        "message_id": event.message_id
    }
    return v


class pic_info():
    def __init__(self, msg, event,  db):
        self.sql_vals = make_pic_baseinfo(msg,  event)
        self.last = None
        self.finished = False
        self.db = db

    def sizeCheck(self):
        img_h = self.sql_vals["img_height"]
        img_w = self.sql_vals["img_width"]
        min_w = conf["minWidth"]
        min_h = conf["minHeight"]
        if img_h and img_w and (img_w < min_w) and (img_h < min_h):
            self.finished = True

    async def url_hash_check(self):
        if self.finished:
            return
        db = self.db
        v = self.sql_vals
        pic_query = alsql.select([
            message_type_pic.c.img_width,
            message_type_pic.c.img_height,
            message_type_pic.c.img_hash
        ]).where(
            message_type_pic.c.url_hash == v["url_hash"]
        ).order_by(
            message_type_pic.c.id.desc()
        )

        pic_query_filter = alsql.select([
            message_type_pic
        ]).where(
            message_type_pic.c.group_id == v["group_id"],
            message_type_pic.c.url_hash == v["url_hash"],
            message_type_pic.c.time > fromTimeStamp()
        ).order_by(
            message_type_pic.c.id.desc()
        )

        query_results = await gather(
            db.fetch_one(query=pic_query),
            db.fetch_one(query=pic_query_filter)
        )

        if query_results[0]:
            row = query_results[0]
            info = {
                "img_width": row.img_width,
                "img_height": row.img_height,
                "img_hash": row.img_hash,
            }
            self.sql_vals.update(info)
            logger.debug(f"sqlvals:{self.sql_vals}")
            self.sizeCheck()
        if self.finished != True:
            if query_results[1]:
                count = query_results[1].count + 1
                info = {
                    "count": count
                }
                self.sql_vals.update(info)
                self.finished = True
                self.last = query_results[1]

    async def fast_size_check(self):
        if self.finished:
            return
        v = self.sql_vals
        try:
            info = await getSizeFast(v["url"])
            self.sql_vals.update(info)
            self.sizeCheck()
        except Exception as err:
            logger.info(f"fast size failed:{err}\npic:{v}")

    async def similar_search_check(self):
        db = self.db
        if self.finished:
            return
        try:
            info = await getImg_WH_Hash(self.sql_vals["url"])
            self.sql_vals.update(info)
        except Exception as err:
            logger.info(f"calc hash failed:{err}\npic:{self.sql_vals}")
            return
        last = await similar_pic_search(self.sql_vals, self.db)
        if last:
            count = last.count+1
            self.sql_vals["count"] = count
            self.last = last
            self.finished = True

    async def update_hash_table(self):
        db = self.db
        v = self.sql_vals
        if v.get("img_hash", None):
            querys = []
            for i in range(4):
                query = {
                    "img_hash": v["img_hash"][i*4:(i+1)*4],
                    "message_id": v["message_id"],
                    "time": v["time"],
                    "group_id": v["group_id"]
                }
                querys.append(query)
            hash_ins_model = message_type_pic_hash.insert()
            await db.execute_many(
                query=hash_ins_model, values=querys)

    async def update_pic(self):
        db = self.db
        v = self.sql_vals
        queryModel = message_type_pic.insert()
        await db.execute(query=queryModel, values=v)

    async def process_full(self):
        await self.url_hash_check()
        await self.fast_size_check()
        await self.similar_search_check()
        await gather(
            self.update_hash_table(), self.update_pic()
        )

#        return self.last


async def pics_process(event, matcher, db):
    msgList = event.get_message()
    imgList = [x for x in msgList if (
        x.type == "image") and x.data.get("subType", -1) == "0"]
    pic_processor = [pic_info(msg, event, db) for msg in imgList]
    tasks = [p.process_full() for p in pic_processor]

    done = await gather(*tasks)

    dup_msgs = []
    displayname = ""
    if event.sender.card:
        displayname = event.sender.card
    else:
        displayname = event.sender.nickname

    bot_msg = f"火星消息警察,对 {displayname} 出警!\r\n"
    bot_msg_after = ""
    for k, v in enumerate(pic_processor):
        if v.last and conf_filter(v):
            bot_msg_after += f"第{k+1} 张由{v.last.user_displayname} 在{mk2Str(v.last.time)} 发过了!\r\n这条消息已经发了{v.last.count+1} 次!\r\n"
    if bot_msg_after:
        final = bot_msg + bot_msg_after
        final = final.strip()
        await matcher.send(final)


def conf_filter(p):
    if not conf["calloutSelf"]:
        if p.last.user_id == p.sql_vals["user_id"]:
            return False
    if conf["cooldown"] > 0:
        timeStr = mk2Str(p.last.time)
        now = int(time.time())
        diff = now - p.last.time
        if (diff < conf["cooldown"]*60):
            return False
    if p.sql_vals["count"] > conf["maxCallout"]:
        return False
    return True
