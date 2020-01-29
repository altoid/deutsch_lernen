import MySQLdb
import MySQLdb.cursors

def getConnection():
    return MySQLdb.connect(user="",
                           passwd="",
                           db="",
                           host="",
                           cursorclass=MySQLdb.cursors.DictCursor)
