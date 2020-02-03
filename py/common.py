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

        # insert the word to get a word id
        q = """
        insert ignore into word (pos_id, word) values (%s, '%s')
        """ % (pos_id, word)
        c.execute(q)

        # fetch the word id
        q = """
        select last_insert_id() as word_id
        """
        c.execute(q)

        row = c.fetchone()
        word_id = row['word_id']

        word_attributes = get_word_attributes(c, pos_id, word_id)
        max_width = get_max_width(word_attributes)

        # pprint(word_id)
        # pprint(word_attributes)
        
        input_values = []
        for r in word_attributes:
            d = {}
            prefix = "--[%s]-->" % r['attrkey']
            prompt = string.ljust(prefix, max_width)
            prompt += "[%s]:" % (
                '' if r['attrvalue'] == None else r['attrvalue'])
                
            v = raw_input(prompt)
            if len(v) > 0:
                d['value'] = v
                d['attribute_id'] = r['attribute_id']

            if len(d) > 0:
                input_values.append(d)

        # pprint(input_values)
        
        # insert into the word_attribute table
        tuples = ["(%s, %s, '%s')" % (iv['attribute_id'], word_id, iv['value']) for iv in input_values]

        # pprint(tuples)
        
        if len(tuples) > 0:
            q = """
            insert into word_attribute(attribute_id, word_id, value) values %s
            on duplicate key update value=values(value)
            """ % ','.join([t for t in tuples])

            # print q
            c.execute(q)
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
    and wa.word_id = %(word_id)s
    where pf.pos_id = %(pos_id)s
    """ % {
        'pos_id': pos_id,
        'word_id': word_id,
        }
    
    c.execute(q)

    word_attributes = []
    for row in c.fetchall():
        word_attributes.append(row)

    return word_attributes

def prompt_word(db, c, pos_id):
    input_string = raw_input('--[word]--> ').strip().lower()

    # TODO:  handle the case where multiple words are given as input - treat as error
    
    if len(input_string) == 0:
        return True

    add_or_update_word(db, c, input_string, pos_id)
