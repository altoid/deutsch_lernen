import string
from pprint import pprint


def get_max_width(word_attributes):
    """
    get the maximum display width of all the attribute keys.
    used for building prompts.
    """

    max_width = max([len(x['attrkey']) for x in word_attributes])
    max_width += 8  # pad for "--[]--> "
    return max_width


def add_or_update_word(db, c, word, pos_id):
    try:
        # start transaction
        c.execute("start transaction")

        q = """
        select id word_id
        from word 
        where pos_id = %s and word = %s
        """

        c.execute(q, (pos_id, word))
        row = c.fetchone()
        if not row:
            # word doesn't exist

            # insert the word to get a word id
            q = """
            insert ignore into word (pos_id, word) values (%s, %s)
            """
            c.execute(q, (pos_id, word))

            # fetch the word id
            q = """
            select last_insert_id() as word_id
            """
            c.execute(q)

            row = c.fetchone()

        word_id = row['word_id']

        word_attributes = get_word_attributes(c, pos_id, word_id)
        max_width = get_max_width(word_attributes)

        input_values = []
        for r in word_attributes:
            prefix = "--[%s]-->" % r['attrkey']
            prompt = prefix.ljust(max_width)
            prompt += "[%s]:" % (
                '' if r['attrvalue'] == None else r['attrvalue'])
            prompt = prompt.encode('utf-8')
            v = input(prompt).strip()
            if len(v) > 0:
                input_values.append((r['attribute_id'], word_id, v))

        if len(input_values) > 0:
            q = """
            insert into word_attribute(attribute_id, word_id, value)
            values (%s, %s, %s)
            on duplicate key update value=values(value)
            """

            # print q
            c.executemany(q, input_values)
            
        db.commit()
    except Exception as e:
        db.rollback()
        raise


def get_word_attributes(c, pos_id, word_id):
    q = """
    select pf.attribute_id, a.attrkey, wa.value attrvalue
    from pos_form pf
    inner join attribute a on a.id = pf.attribute_id
    left join word_attribute wa
    on wa.attribute_id = pf.attribute_id
    and wa.word_id = %s
    where pf.pos_id = %s
    order by pf.sort_order
    """

    c.execute(q, (word_id, pos_id))

    word_attributes = c.fetchall()

    return word_attributes


def prompt_word(db, c, pos_id):
    input_string = input('--[word]--> ').strip().lower()

    # TODO:  handle the case where multiple words are given as input - treat as error

    if len(input_string) == 0:
        return True

    add_or_update_word(db, c, input_string, pos_id)
