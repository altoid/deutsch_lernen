import common

articles=['der','die','das']

# prompt for article and word
def get_word_with_article(db, dasWort):

    stuff = dasWort.split()

    if len(stuff) != 2:
        return None

    if not stuff[0] in articles:
        return None

    article = db.escape_string(stuff[0])
    noun = db.escape_string(stuff[1])

    r = {'article' : article,
         'word' : noun }

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
 wa.value = '%s' and
 pos2.name = pos.name and
 pos.id = w.pos_id and
 w.word = '%s' and
 w.id = wa.word_id
)
where
 pos.name = 'Noun'

""" % (noundict['article'], noundict['word'])

    c.execute(q)

    r = []
    for row in c.fetchall():
        d = dict(zip(['pos_name', 'pos_id', 'attribute_id', 'attrkey', 'word_id', 'value'],
                     row))

        if d['attrkey'] == 'article' and d['value'] == None:
            # abort
            return []

        r.append(d)

    return r

def insert_word(db, c, input_word):

    # fetch all the attributes for nouns
    word_attributes = common.get_pos_attributes(c, 'Noun')

    pos_id = word_attributes[0]['pos_id']

    input_values = []

    tuples = []
    for r in word_attributes:
        d = {}
        if r['attrkey'] == 'article':
            d['value'] = input_word['article']
            d['attribute_id'] = r['attribute_id']
        else:
            v = raw_input( "--[%s]--> " % (r['attrkey'])).strip().lower()
            v = db.escape_string(v)
            v = unicode(v, 'utf8')
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

    # get the word id - we know it's associated with the article
    word_id = None
    for r in word_attributes:
        if r['attrkey'] == 'article':
            word_id = r['word_id']
            break

    for r in word_attributes:
        if r['attrkey'] == 'article':
            continue

        prompt = "--[%s]--> [%s]:" % (r['attrkey'], '' if r['value'] == None else r['value'])

        v = raw_input(prompt).strip().lower()
        v = db.escape_string(v)
        v = unicode(v, 'utf8')
        if len(v) > 0 and r['value'] != v:
            tuple = "(%s, %s, '%s')" % (r['attribute_id'], word_id, v)
            tuples.append(tuple)
            
    if len(tuples) == 0:
        print "no new data, returning"
        return

    # start transaction
    q = ','.join([x for x in tuples])

    query = """
insert into word_attribute(attribute_id, word_id, value) values %s
on duplicate key update value=values(value)
""" % q

    c.execute(query)
    db.commit()

def prompt_noun(db, c):

    while True:
        input_string = raw_input('--[noun with article]--> ').strip().lower()

        if len(input_string) == 0:
            return True

        input_word = get_word_with_article(db, input_string)
        if input_word is not None:
            break

        print 'falsches input'

    word_attributes = get_noun_info(c, input_word)

    if len(word_attributes) == 0:
        insert_word(db, c, input_word)
    else:
        update_word(db, c, word_attributes)

    return False
