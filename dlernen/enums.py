from enum import EnumType, StrEnum
from contextlib import closing
from mysql.connector import connect
from pprint import pprint, pformat


def create_quizkey_class(app):
    class_name = "QuizKey"
    bases = (StrEnum,)  # Base classes must be inside a tuple

    # 1. Prepare the specialized EnumDict namespace required by EnumType
    class_dict = EnumType.__prepare__(class_name, bases)

    # 2. Inject values from database as static enum members
    with app.app_context():
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = """
                select quiz_key
                from quiz
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            values_dict = {x['quiz_key'].upper(): x['quiz_key'] for x in rows}

            # note:  class_dict is an _EnumDict, so the |= operator won't work.  but .update() works fine.
            class_dict.update(values_dict)

            # Construct the class safely using EnumType
            return EnumType(class_name, bases, class_dict)


def create_posname_class(app):
    class_name = "QuizKey"
    bases = (StrEnum,)  # Base classes must be inside a tuple

    # 1. Prepare the specialized EnumDict namespace required by EnumType
    class_dict = EnumType.__prepare__(class_name, bases)

    # 2. Inject values from database as static enum members
    with app.app_context():
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = """
                select name pos_name
                from pos
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            values_dict = {x['pos_name'].replace(' ', '_').upper(): x['pos_name'] for x in rows}

            # note:  class_dict is an _EnumDict, so the |= operator won't work.  but .update() works fine.
            class_dict.update(values_dict)

            # Construct the class safely using EnumType
            return EnumType(class_name, bases, class_dict)


def create_attrkey_class(app):
    class_name = "AttrKey"
    bases = (StrEnum,)  # Base classes must be inside a tuple

    # 1. Prepare the specialized EnumDict namespace required by EnumType
    class_dict = EnumType.__prepare__(class_name, bases)

    # 2. Inject values from database as static enum members
    with app.app_context():
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = """
                select attrkey
                from attribute
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            values_dict = {x['attrkey'].replace(' ', '_').upper(): x['attrkey'] for x in rows}

            # note:  class_dict is an _EnumDict, so the |= operator won't work.  but .update() works fine.
            class_dict.update(values_dict)

            # Construct the class safely using EnumType
            return EnumType(class_name, bases, class_dict)
