from pydantic import BaseSettings


class Config(BaseSettings):
    # Your Config Here

    class Config:
        extra = "ignore"


gloabal_conf = {
    "calloutSelf": False,
    "maxCallout": 10,
    "minTextLength": 128,
    "cooldown": 3,
    "minWidth": 512,
    "minHeight": 512,
    "searchRange": {
        "count": 5000,
        "days": 30
    }
}