import string

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
            word_id = row['word_id']
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
    old_q = """
select
        pos.name,
        pos.id pos_id,
        a.id attribute_id,
        a.attrkey,
        '%(word)s' word,
        word.id word_id,
        wa.value attrvalue
from
	pos
	inner join pos_form pf on pos.id = pf.pos_id
	inner join attribute a on a.id = pf.attribute_id
	left join word on word.pos_id = pos.id and word.word = '%(word)s'
	left join words_x_attributes_v v on v.pos_id = pos.id and v.attribute_id = a.id and v.word_id = word.id
	left join word_attribute wa on wa.attribute_id = v.attribute_id and wa.word_id = v.word_id
where
	pos.name = '%(posname)s'
order by pf.sort_order
""" % { "word" : word,
        "posname" : posname }

    q = """
select
        pos.name,
        pos.id pos_id,
        a.id attribute_id,
        a.attrkey,
        '%(word)s' word,
        word.id word_id,
        wa.value attrvalue
from
	pos
	inner join pos_form pf on pos.id = pf.pos_id
	inner join attribute a on a.id = pf.attribute_id
	left join word on word.pos_id = pos.id
	left join words_x_attributes_v v on v.pos_id = pos.id and v.attribute_id = a.id and v.word_id = word.id
	left join word_attribute wa on wa.attribute_id = v.attribute_id and wa.word_id = v.word_id
where
	word.word = '%(word)s'
order by pf.sort_order
""" % { "word" : word }

    print q
    c.execute(q)

    word_attributes = []
    for row in c.fetchall():
        word_attributes.append(row)

    return word_attributes

def prompt_word(db, c, posname):
    input_string = raw_input('--[word]--> ').strip().lower()

    if len(input_string) == 0:
        return True

    word_attributes = get_word_attributes(c, posname, input_word)

    add_or_update_word(db, c, word_attributes)
