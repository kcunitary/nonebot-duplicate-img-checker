from datetime import datetime,timedelta
from .config import gloabal_conf

conf = gloabal_conf

def fromTimeStamp():
    confdays = conf["searchRange"]["days"]
    daysdelta = timedelta(days=confdays)
    fromday = datetime.today() - daysdelta
    fromTimeStamp = int(fromday.timestamp())
    return fromTimeStamp

def mk2Str(mk):
    t = datetime.fromtimestamp(mk)
    text = datetime.strftime(t, r"%m-%d %H:%M:%S")
    return text