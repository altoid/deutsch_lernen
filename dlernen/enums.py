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

    class_dict = EnumType.__prepare__(class_name, bases)

    # 2. Inject the custom __new__ method directly
    def __new__(cls, value, attr_id=None):
        obj = str.__new__(cls, value)
        obj._value_ = value
        obj._attribute_id = attr_id
        return obj

    class_dict["__new__"] = __new__

    # 3. Inject the custom db_id property directly
    @property
    def attribute_id(self):
        return self._attribute_id

    class_dict["attribute_id"] = attribute_id

    def get_id(cls, value):
        """
        Pass a raw string value (e.g., 'definition').
        Returns the database ID if found, or None if it doesn't exist.
        """

        # throws ValueError if the string value isn't an enum member!

        # Enums natively allow looking up a member by its value: cls("Color")
        member = cls(value)
        return member.attribute_id

    # wrap it in classmethod() explicitly when assigning it to the dict
    class_dict["get_id"] = classmethod(get_id)

    # Inject values from database as static enum members
    with app.app_context():
        with closing(connect(**app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
            sql = """
                select attrkey, id attribute_id
                from attribute
            """
            cursor.execute(sql)
            rows = cursor.fetchall()

            # 4. Populate the database enum members
            # EnumDict will catch duplicate keys or invalid names here natively.
            for row in rows:
                key = row["attrkey"].upper().replace(" ", "_")
                # Map the key to a tuple: (string_value, integer_id)
                class_dict[key] = (row["attrkey"], row["attribute_id"])

            # Construct the class safely using EnumType
            return EnumType(class_name, bases, class_dict)

