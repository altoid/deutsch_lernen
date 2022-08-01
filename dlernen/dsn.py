import mysql.connector
from dlernen.config import Config


def getConnection():
    return mysql.connector.connect(host=Config.MYSQL_HOST,
                                   user=Config.MYSQL_USER,
                                   passwd=Config.MYSQL_PASS,
                                   db=Config.MYSQL_DB,
                                   use_unicode=True, charset="utf8")
