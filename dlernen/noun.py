import logging

articles = ['der', 'die', 'das']


# prompt for article and word
def get_word_with_article(db, dasWort):
    """
    returns word and the article in a dictionary,
    keys are 'article' and 'word'
    """

    stuff = dasWort.split()

    if len(stuff) != 2:
        return None

    if not stuff[0] in articles:
        return None

    article = stuff[0]
    noun = str(stuff[1], 'utf8')

    r = {'article': article,
         'word': noun}

    return r


# noundict is the noun info typed in.
# look for it.  if it's not in the database,
# return empty dict.  if it is in the 
# database, return list of dicts with all the attribute values.
def get_noun_info(c, noundict):
    # find the word id of the noun whose word and article are given.
    # using that word id, find all the values for the attributes of that
    # noun.
    #
    # beware:  if the article/word is not present, we will still get
    # rows, but all the values will all be null.  so if we get no value
    # for the article, we know it's not in the database.

    q = """

select pos.name, pos_form.pos_id, pos_form.attribute_id, a.attrkey, wa.word_id, wa.value from pos
inner join pos_form on pos.id = pos_form.pos_id
inner join attribute a on pos_form.attribute_id = a.id
left join word_attribute wa on wa.attribute_id = a.id and word_id = 
(
select w.id from pos pos2, attribute a, word w, word_attribute wa 
where a.attrkey = 'article' and    
 a.id = wa.attribute_id and 
 wa.value = %s and
 pos2.name = pos.name and
 pos.id = w.pos_id and
 w.word = %s and
 w.id = wa.word_id
)
where
 pos.name = 'Noun'

"""

    c.execute(q, (noundict['article'], noundict['word']))

    r = []
    for row in c.fetchall():
        if row['attrkey'] == 'article' and row['value'] is None:
            # abort
            return []

        r.append(row)

    return r


def insert_word(db, c, input_word):
    # fetch all the attributes for nouns
    q = """
select
	attribute.attrkey, attribute.id attribute_id, pos_form.pos_id
from
	pos
inner join pos_form on pos.id = pos_form.pos_id
inner join attribute on pos_form.attribute_id = attribute.id
where
	pos.name = 'noun'
"""
    c.execute(q)
    word_attributes = c.fetchall()

    pos_id = word_attributes[0]['pos_id']

    input_values = []

    tuples = []
    for r in word_attributes:
        d = {}
        if r['attrkey'] == 'article':
            d['value'] = input_word['article']
            d['attribute_id'] = r['attribute_id']
        else:
            value = input("--[%s]--> " % (r['attrkey'])).strip().lower()
            value = str(value, 'utf8')
            if len(value) > 0:
                if r['attrkey'] == 'plural':
                    value = value.capitalize()
                d['value'] = value
                d['attribute_id'] = r['attribute_id']

        if len(d) > 0:
            input_values.append(d)

    # start transaction
    c.execute("start transaction")

    # insert into the word table
    q = """
insert into word (pos_id, word) values (%s, %s)
"""
    c.execute(q, (pos_id, input_word['word'].capitalize()))

    # fetch the word id
    word_id = None
    q = """
select last_insert_id() as word_id
"""
    c.execute(q)

    row = c.fetchone()
    word_id = row['word_id']

    logging.debug("inserted '%s', id = %s" % (
        input_word['word'], word_id))

    # insert into the word_attribute table
    tuples = []
    for iv in input_values:
        tuples.append((iv['attribute_id'], word_id, iv['value']))

    q = """
insert into word_attribute (attribute_id, word_id, value)
values
(%s, %s, %s)
"""

    c.executemany(q, tuples)
    db.commit()


def update_word(db, c, word_attributes):
    # get the word id - we know it's associated with the article
    word_id = None
    for r in word_attributes:
        if r['attrkey'] == 'article':
            word_id = r['word_id']
            break

    tuples = []
    for r in word_attributes:
        if r['attrkey'] == 'article':
            continue

        prompt = "--[%s]--> [%s]:" % (r['attrkey'], '' if r['value'] is None else r['value'])
        prompt = prompt.encode('utf-8')
        value = input(prompt).strip().lower()
        value = str(value, 'utf8')
        if len(value) > 0 and r['value'] != value:
            if r['attrkey'] == 'plural':
                value = value.capitalize()

            tuples.append((r['attribute_id'], word_id, value))

    if len(tuples) == 0:
        print("no new data, returning")
        return

    # start transaction

    query = """
insert into word_attribute(attribute_id, word_id, value) 
values (%s, %s, %s)
on duplicate key update value=values(value)
"""

    c.executemany(query, tuples)
    db.commit()


def prompt_noun(db, c):
    while True:
        input_string = input('--[noun with article]--> ').strip().lower()

        if len(input_string) == 0:
            return True

        input_word = get_word_with_article(db, input_string)
        if input_word is not None:
            break

        print('falsches input')

    word_attributes = get_noun_info(c, input_word)

    if len(word_attributes) == 0:
        insert_word(db, c, input_word)
    else:
        update_word(db, c, word_attributes)

    return False