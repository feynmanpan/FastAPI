import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
import databases
#
import redis
####################################################


# 由main的startup啟動連線 # await dbwtb.connect()
DB_URL = "postgresql://pan:pgcode@localhost/wtb"
# 三個提供給外部使用
dbwtb = databases.Database(DB_URL, ssl=False)
metadata = sa.MetaData()
Base = declarative_base()
#
init = {
    "host": 'localhost',
    "port": 6379,
    "db": 0,
    "password": 'redispwd',
    "decode_responses": True,
}
#
r_redis = redis.StrictRedis(**init)
