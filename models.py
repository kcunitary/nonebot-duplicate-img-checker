from databases import Database
import sqlalchemy


metadata = sqlalchemy.MetaData()

group_message_meta = sqlalchemy.Table(
    "group_message_event",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger,
                      autoincrement=True, primary_key=True),

    sqlalchemy.Column("self_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("sub_type", sqlalchemy.VARCHAR(length=255)),

    sqlalchemy.Column("message_type", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("message_id", sqlalchemy.BigInteger,index=True),
    sqlalchemy.Column("font", sqlalchemy.Integer),
    sqlalchemy.Column("to_me", sqlalchemy.Boolean),

    sqlalchemy.Column("time", sqlalchemy.Integer),
    sqlalchemy.Column("user_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("group_id", sqlalchemy.BigInteger)
)

group_message_sender = sqlalchemy.Table(
    "group_message_sender",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger,
                      autoincrement=True, primary_key=True),
    sqlalchemy.Column("user_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("nickname", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("sex", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("age", sqlalchemy.Integer),
    sqlalchemy.Column("card", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("area", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("level", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("role", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("title", sqlalchemy.VARCHAR(length=255)),


    sqlalchemy.Column("user_displayname", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("time", sqlalchemy.Integer),
    sqlalchemy.Column("group_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("message_id", sqlalchemy.BigInteger)
)


message_type_text = sqlalchemy.Table(
    "message_type_text",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger,
                      autoincrement=True, primary_key=True),
    sqlalchemy.Column("plain_text", sqlalchemy.VARCHAR(length=5000)),
    sqlalchemy.Column("message", sqlalchemy.JSON),
    sqlalchemy.Column("text_length", sqlalchemy.Integer),

    sqlalchemy.Column("count", sqlalchemy.Integer),

    sqlalchemy.Column("time", sqlalchemy.Integer),
    sqlalchemy.Column("user_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("user_displayname", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("group_id", sqlalchemy.BigInteger),

    sqlalchemy.Column("message_id", sqlalchemy.BigInteger)
)

message_type_pic = sqlalchemy.Table(
    "message_type_pic",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger,
                      autoincrement=True, primary_key=True),
    sqlalchemy.Column("url", sqlalchemy.VARCHAR(length=5000)),


    sqlalchemy.Column("url_hash", sqlalchemy.VARCHAR(length=255),index=True),
    sqlalchemy.Column("img_width", sqlalchemy.Integer),
    sqlalchemy.Column("img_height", sqlalchemy.Integer),
    sqlalchemy.Column("img_hash", sqlalchemy.CHAR(length=16)),
    sqlalchemy.Column("ocr_text", sqlalchemy.VARCHAR(length=2083)),
    sqlalchemy.Column("ocr_len", sqlalchemy.Integer),
    sqlalchemy.Column("count", sqlalchemy.Integer),

    sqlalchemy.Column("time", sqlalchemy.Integer),
    sqlalchemy.Column("user_id", sqlalchemy.BigInteger),

    sqlalchemy.Column("user_displayname", sqlalchemy.VARCHAR(length=255)),
    sqlalchemy.Column("group_id", sqlalchemy.BigInteger),

    sqlalchemy.Column("message_id", sqlalchemy.BigInteger,index=True)
)
sqlalchemy.schema.Index("url_repeated_search",message_type_pic.c.group_id,message_type_pic.c.url_hash,message_type_pic.c.time)
message_type_pic_hash = sqlalchemy.Table(
    "message_type_pic_hash",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.BigInteger,
                      autoincrement=True, primary_key=True),
    sqlalchemy.Column("img_hash", sqlalchemy.CHAR(4)),
    sqlalchemy.Column("group_id", sqlalchemy.BigInteger),
    sqlalchemy.Column("time", sqlalchemy.Integer),
    sqlalchemy.Column("message_id", sqlalchemy.BigInteger)
)
sqlalchemy.schema.Index("hash_repeated_search",
message_type_pic_hash.c.group_id,message_type_pic_hash.c.time,message_type_pic_hash.c.img_hash)


def main():
    mysqlUrl = "mysql+pymysql://"
    """ database = Database(mysqlUrl)
    Establish the connection pool
    await database.connect()
    await database.disconnect() """
    engine = sqlalchemy.create_engine(mysqlUrl, echo=True)
    metadata.create_all(engine)
    with engine.connect() as conn:
        result = conn.execute(sqlalchemy.text(
            "ALTER TABLE message_type_text ADD FULLTEXT(plain_text);"))


if __name__ == "__main__":
    #    print(1)
    main()
