import string

def get_word(db, dasWort):

    word = db.escape_string(dasWort)

    r = {'word' : word }

    return r

# worddict is the word info typed in.
# look for it.  if it's not in the database,
# return empty dict.  if it is in the 
# database, return list of dicts with all the attribute values.
def get_word_info(c, worddict, posname):

    # find the word id of the given word.
    # using that word id, find all the values for the attributes of that
    # word.
    #
    # beware:  if the word is not present, we will still get
    # rows, but all the values will all be null.  so if we get no value
    # for the wa.value column, we know it's not in the database.

    q = """

 select
 	pos.name,
 	pos.id pos_id,
 	v.attribute_id,
 	a.attrkey,
 	wa.word_id,
 	wa.value
 from words_x_attributes_v v   -- pos_id, word_id, attribute_id
 inner join pos on pos.id = v.pos_id
 inner join attribute a on a.id = v.attribute_id
 inner join pos_form on pos_form.pos_id = v.pos_id and pos_form.attribute_id = v.attribute_id
 inner join word on word.id = v.word_id
 left join word_attribute wa on v.word_id = wa.word_id and v.attribute_id = wa.attribute_id
 where word.word = '%s'
 and pos.name = '%s'
 order by v.word_id, pos_form.sort_order

""" % (worddict['word'], posname)

    c.execute(q)

    any_attributes_defined = False
    r = []
    for row in c.fetchall():
        d = dict(zip(['pos_name', 'pos_id', 'attribute_id', 'attrkey', 'word_id', 'value'],
                     row))

        if d['value'] != None:
            any_attributes_defined = True

        r.append(d)

    return r if any_attributes_defined else []

def get_pos_attributes(c, pos):

    q = """
select pos.name, pos_form.pos_id, pos_form.attribute_id, attribute.attrkey
from
pos, pos_form, attribute where pos.id = pos_form.pos_id
  and pos_form.attribute_id = attribute.id and pos.name = '%s'
order by pos_form.sort_order
""" % (pos)

    c.execute(q)

    word_attributes = []
    for row in c.fetchall():
        d = dict(zip(['pos_name', 'pos_id', 'attribute_id', 'attrkey'],
                     row))

        word_attributes.append(d)

    return word_attributes

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

def insert_word(db, c, input_word, posname):

    # fetch all the attributes for word
    word_attributes = get_pos_attributes(c, posname)

    max_width = get_max_width(word_attributes)

    pos_id = word_attributes[0]['pos_id']

    input_values = []

    tuples = []
    for r in word_attributes:
        d = {}
        prefix = "--[%s]-->" % r['attrkey']
        prompt = string.ljust(prefix, max_width)

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
    q = """
insert into word (pos_id, word) values (%s, '%s')
""" % (pos_id, input_word['word'])
    c.execute(q)

    # fetch the word id
    word_id = None
    q = """
select last_insert_id() as word_id
"""
    c.execute(q)

    for row in c.fetchall():
        word_id = row[0]
        break

    # insert into the word_attribute table
    tuples = []
    for iv in input_values:
        t = "(%s, %s, '%s')" % (iv['attribute_id'], word_id, iv['value'])
        tuples.append(t)

    q = """
insert into word_attribute (attribute_id, word_id, value)
values
%s
""" % ','.join([t for t in tuples])

    c.execute(q)
    db.commit()


def update_word(db, c, word_attributes):

    tuples = []

    word_id = None
    for r in word_attributes:
        if r['word_id'] != None:
            word_id = r['word_id']
            break

    max_width = get_max_width(word_attributes)

    for r in word_attributes:
        prefix = "--[%s]-->" % r['attrkey']
        prompt = "%s [%s]:" % (
            string.ljust(prefix, max_width),
            '' if r['value'] == None else r['value'])
        v = raw_input(prompt)
        v = unicode(v, 'utf8').strip().lower()
        if len(v) > 0 and r['value'] != v:
            tuple = "(%s, %s, '%s')" % (r['attribute_id'], word_id, v)
            tuples.append(tuple)
            
    if len(tuples) == 0:
        return

    # start transaction
    q = ','.join([x for x in tuples])

    query = """
insert into word_attribute(attribute_id, word_id, value) values %s
on duplicate key update value=values(value)
""" % q

    c.execute(query)
    db.commit()

def prompt_word(db, c, posname):
    input_string = raw_input('--[word]--> ').strip().lower()

    if len(input_string) == 0:
        return True

    input_word = get_word(db, input_string)

    word_attributes = get_word_info(c, input_word, posname)

    if len(word_attributes) == 0:
        insert_word(db, c, input_word, posname)
    else:
        update_word(db, c, word_attributes)

    return False
