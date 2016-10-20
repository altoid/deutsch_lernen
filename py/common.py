import string
import logging

logging.basicConfig(level=logging.DEBUG)

def get_max_width(word_attributes):
    """
    get the maximum display width of all the attribute keys.
    used for building prompts.
    """

    max_width = 0
    for r in word_attributes:
        if len(r['attrkey']) > max_width:
            max_width = len(r['attrkey'])
            
    max_width += 8  # pad for "--[]--> "
    return max_width

def add_or_update_word(db, c, word_attributes):

    max_width = get_max_width(word_attributes)

    word_id = word_attributes[0]['word_id']
    pos_id = word_attributes[0]['pos_id']
    input_word = word_attributes[0]['word']
    input_values = []

    tuples = []
    for r in word_attributes:
        d = {}
        prefix = "--[%s]-->" % r['attrkey']
        prompt = string.ljust(prefix, max_width)
        if word_id: 
            prompt += "[%s]:" % (
                '' if r['attrvalue'] == None else r['attrvalue'])

        v = raw_input(prompt)
        v = db.escape_string(v)
        if len(v) > 0:
            d['value'] = v
            d['attribute_id'] = r['attribute_id']

        if len(d) > 0:
            input_values.append(d)

    # start transaction
    c.execute("start transaction")

    # insert into the word table
    if not word_id:
        q = """
insert into word (pos_id, word) values (%s, '%s')
""" % (pos_id, input_word)
        c.execute(q)

        # fetch the word id
        q = """
select last_insert_id() as word_id
"""
        c.execute(q)

        for row in c.fetchall():
            word_id = row[0]
            break

    # insert into the word_attribute table
    tuples = ["(%s, %s, '%s')" % (iv['attribute_id'], word_id, iv['value']) for iv in input_values]

    if len(tuples) > 0:
        q = """
insert into word_attribute(attribute_id, word_id, value) values %s
on duplicate key update value=values(value)
""" % ','.join([t for t in tuples])

        c.execute(q)

    db.commit()

def get_word_attributes(c, posname, word):
    q = """
select
        pos_name,
        pos_id,
        attribute_id,
        attrkey,
        '%(word)s' word,
        word_id,
        attrvalue,
        sort_order
from
    mashup
where
	pos_name = '%(posname)s'
    and word = '%(word)s'
order by sort_order
""" % { "word" : word,
        "posname" : posname }

    c.execute(q)

    word_attributes = []
    for row in c.fetchall():
        d = dict(zip(['pos_name', 'pos_id', 'attribute_id', 'attrkey', 'word', 'word_id', 'attrvalue'],
                     row))
        word_attributes.append(d)

    return word_attributes

def prompt_word(db, c, posname):
    input_string = raw_input('--[word]--> ').strip().lower()

    if len(input_string) == 0:
        return True

    input_word = db.escape_string(input_string)

    word_attributes = get_word_attributes(c, posname, input_word)

    add_or_update_word(db, c, word_attributes)
