import mysql.connector

def getConnection():
    return mysql.connector.connect(user="",
                                   passwd="",
                                   db="",
                                   host="",
                                   use_unicode=True, charset="utf8")
