import MySQLdb
import MySQLdb.cursors

def getConnection():
    return MySQLdb.connect(user="",
                           passwd="",
                           db="",
                           host="",
                           use_unicode=True, charset="utf8",
                           cursorclass=MySQLdb.cursors.DictCursor)
