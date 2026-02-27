import mysql.connector.errors
from flask import Blueprint, request, current_app
from pprint import pprint
from mysql.connector import connect
from dlernen import dlernen_json_schema, common

from contextlib import closing
import jsonschema

# view functions for /api/wordlist URLs are here.

bp = Blueprint('api_wordlist', __name__, url_prefix='/api/wordlist')

SQL_FOR_WORDLIST_FROM_SQLCODE = """
    with matching as ( %s )
    select
          m.word word,
          matching.word_id,
          m.attrvalue definition,
          ifnull(m2.attrvalue, '') article
    from  matching
    left  join mashup_v m
    on    matching.word_id = m.word_id
    and   m.attrkey = 'definition'
    left  join mashup_v m2
    on    matching.word_id = m2.word_id
    and   m2.attrkey = 'article'
    order by m.word        
"""

SQL_TO_VALIDATE_SQLCODE = """
    with matching as ( %s )
    select word_id
    from matching
"""


def validate_sqlcode(cursor, sqlcode):
    # throw an exception if the sqlcode snippet isn't useful for constructing a wordlist.
    # has to be called from within a context manager block; we won't make a new database
    # connection for this.

    if sqlcode is not None:
        x = sqlcode.strip()
        sql = SQL_TO_VALIDATE_SQLCODE % x

        cursor.execute(sql)

        # if we don't do a fetch we will get an incomplete read.
        cursor.fetchall()


def __get_wordlist_metadata(wordlist_id):
    """
    returns the metadata for a given wordlist:  name, sqlcode, citation, list_type, and id.
    """
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
        id wordlist_id, name, citation, sqlcode
        from wordlist
        where id = %s
        """
        cursor.execute(sql, (wordlist_id,))
        wl_metadata = cursor.fetchone()

        # see if there are any known or unknown words in this wordlist
        sql = """
        select count(*) nwords from (
            select wordlist_id from wordlist_word where wordlist_id = %(wordlist_id)s) a  
        """ % {
            "wordlist_id": wordlist_id
        }
        cursor.execute(sql)
        row = cursor.fetchone()
        nwords = row['nwords']

        # don't validate sqlcode.  callers and wrapper functions should do that.
        # sqlcode may not be valid, but we don't validate on read, so it's out of our hands here.  we need to be
        # able to return list metadata even if it has broken sqlcode, so that clients may fix it.
        if wl_metadata:
            if wl_metadata['sqlcode']:
                wl_metadata['list_type'] = 'smart'
            elif nwords > 0:
                wl_metadata['list_type'] = 'standard'
            else:
                wl_metadata['list_type'] = 'empty'

            jsonschema.validate(wl_metadata, dlernen_json_schema.WORDLIST_METADATA_RESPONSE_SCHEMA)

        # could be None
        return wl_metadata


@bp.route('/<int:wordlist_id>/metadata')
def get_wordlist_metadata(wordlist_id):
    try:
        result = __get_wordlist_metadata(wordlist_id)
        if not result:
            return "wordlist %s not found" % wordlist_id, 404

        # __get_wordlist_metadata validates the object it returns so we don't have to do it here.

        return result
    except jsonschema.ValidationError as f:
        # responses that don't validate are a server implementation problem.
        return str(f), 500


@bp.route('/metadata', methods=['POST'])
def create_wordlist_metadata():
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    name = payload.get('name')
    citation = payload.get('citation')
    sqlcode = payload.get('sqlcode')

    # no need to strip the name; no leading/trailing whitespace is enforced by schema.  however, name is optional
    # in the schema but required here.
    if not name:
        return "wordlists must have a name", 400

    # name is required, but the schema permits no name
    # the json schema enforces that the name has no leading/trailing whitespace, so no need to check for that here.

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        # this is well-behaved if citation and sqlcode are not given.

        try:
            validate_sqlcode(cursor, sqlcode)
            cursor.execute('start transaction')
            sql = "insert into wordlist (`name`, `citation`, `sqlcode`) values (%s, %s, %s)"
            cursor.execute(sql, (name, citation, sqlcode))
            cursor.execute("select last_insert_id() wordlist_id")
            result = cursor.fetchone()
            wordlist_id = result['wordlist_id']
            cursor.execute('commit')
            result = __get_wordlist_metadata(wordlist_id)

            # __get_wordlist_metadata validates the object it returns so we don't have to do it here.

            return result, 201

        except mysql.connector.errors.ProgrammingError as f:
            # if validation of sqlcode that is read from the database fails,
            # treat it as unprocessable content.
            return str(f), 422
        except Exception as e:
            cursor.execute('rollback')
            return "create list failed", 500


@bp.route('/<int:wordlist_id>/metadata', methods=['PUT'])
def update_wordlist_metadata(wordlist_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_METADATA_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # don't update anything that isn't in the payload.
    update_args = {}

    if 'name' in payload:
        update_args['name'] = payload.get('name')

    if 'citation' in payload:
        update_args['citation'] = payload.get('citation')

    if 'sqlcode' in payload:
        update_args['sqlcode'] = payload.get('sqlcode')

    if update_args:
        try:
            wordlist_metadata = __get_wordlist_metadata(wordlist_id)

            with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
                # this is well-behaved if citation and sqlcode are not given.

                if 'sqlcode' in update_args:
                    if wordlist_metadata['list_type'] == 'standard' and update_args['sqlcode']:
                        return "can't add sqlcode to a nonempty list", 400

                    validate_sqlcode(cursor, update_args['sqlcode'])

                cursor.execute('start transaction')
                update_args['wordlist_id'] = wordlist_id

                keez = ['name', 'citation', 'sqlcode']
                clauses = []
                for k in keez:
                    if k in update_args:
                        clauses.append('`%(key)s` = %%(%(key)s)s' % {'key': k})

                sql = """
                update wordlist
                set %(clauses)s
                where id = %%(wordlist_id)s
                """ % {'clauses': ', '.join(clauses)}

                cursor.execute(sql, update_args)
                cursor.execute('commit')

        except mysql.connector.errors.ProgrammingError as e:
            # this will happen if validate_sqlcode throws exception
            return str(e), 422
        except Exception as e:
            cursor.execute('rollback')
            return "update list failed", 500

    # __get_wordlist_metadata validates the object it returns so we don't have to do it here.
    return __get_wordlist_metadata(wordlist_id)


def check_word_ids(word_ids):
    # make sure these word ids exist in the word table; return set of word_ids that are NOT in the word table.

    if not word_ids:
        return set()

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        id_args = ', '.join(['%s'] * len(word_ids))
        sql = """
        select id word_id
        from word
        where id in (%(id_args)s)
        """ % {'id_args': id_args}

        cursor.execute(sql, word_ids)
        rows = cursor.fetchall()
        known_ids = {x['word_id'] for x in rows}
        unknown_ids = set(word_ids) - known_ids

        return unknown_ids


def __get_wordlist(wordlist_id, tags=None):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        sql = """
        select
            id wordlist_id,
            name,
            citation,
            notes,
            sqlcode
        from wordlist
        where id = %s
        """
        cursor.execute(sql, (wordlist_id,))
        wl_row = cursor.fetchone()
        if not wl_row:
            return None

        sqlcode = wl_row['sqlcode']
        citation = wl_row['citation']
        if citation is not None:
            citation = citation.strip()

        result = dict(wl_row)
        result['source_is_url'] = citation.startswith('http') if citation else False

        if sqlcode:
            words_sql = SQL_FOR_WORDLIST_FROM_SQLCODE % sqlcode

            cursor.execute(words_sql)
            rows = cursor.fetchall()
            result['words'] = [
                {
                    'article': r['article'],
                    'definition': r['definition'],
                    'word': r['word'],
                    'word_id': r['word_id'],
                    'tags': []
                }
                for r in rows
            ]

        else:
            if tags:
                tags = set(tags)  # remove any dups
                tag_args = ', '.join(["%s"] * len(tags))
                words_sql = """
                select
                    m.word,
                    m.word_id,
                    m.attrvalue definition,
                    ifnull(m2.attrvalue, '') article,
                    tag.tag
                from wordlist_word ww
                left join mashup_v m
                on   ww.word_id = m.word_id
                and  m.attrkey = 'definition'
                left join mashup_v m2
                on   ww.word_id = m2.word_id
                and  m2.attrkey = 'article'
                
                inner join tag on ww.wordlist_id = tag.wordlist_id and ww.word_id = tag.word_id
                
                where ww.wordlist_id = %%s
                and tag.tag in (%(tag_args)s)
                order by m.word
                """ % {
                    "tag_args": tag_args
                }
                cursor.execute(words_sql, (wordlist_id, *tags))
                words = cursor.fetchall()
            else:
                words_sql = """
                select
                    m.word,
                    m.word_id,
                    m.attrvalue definition,
                    ifnull(m2.attrvalue, '') article,
                    ifnull(tag.tag, '') tag
                from wordlist_word ww
                
                left join mashup_v m
                on   ww.word_id = m.word_id
                and  m.attrkey = 'definition'
                
                left join mashup_v m2
                on   ww.word_id = m2.word_id
                and  m2.attrkey = 'article'
    
                left join tag 
                on ww.wordlist_id = tag.wordlist_id 
                and ww.word_id = tag.word_id
    
                where ww.wordlist_id = %s
                order by m.word
                """

                cursor.execute(words_sql, (wordlist_id,))
                words = cursor.fetchall()

            word_data = {(r['word'], r['word_id']): {
                'article': r['article'],
                'definition': r['definition'],
                'word': r['word'],
                'word_id': r['word_id'],
                'tags': []
            }
                for r in words}
            for r in words:
                if r['tag']:
                    word_data[(r['word'], r['word_id'])]['tags'].append(r['tag'])

            result['words'] = list(word_data.values())

        if sqlcode:
            result['list_type'] = "smart"
        elif words:
            result['list_type'] = "standard"
        else:
            result['list_type'] = "empty"

        jsonschema.validate(result, dlernen_json_schema.WORDLIST_RESPONSE_SCHEMA)

        return result


@bp.route('/<int:wordlist_id>')
def get_wordlist(wordlist_id):
    try:
        tags = request.args.getlist('tag')
        result = __get_wordlist(wordlist_id, tags)
        if result:
            return result

        return "wordlist %s not found" % wordlist_id, 404
    except mysql.connector.errors.ProgrammingError as f:
        # this will happen if the sqlcode is invalid.
        # treat it as unprocessable content.
        return str(f), 422
    except jsonschema.ValidationError as f:
        # responses that don't validate are a server implementation problem.
        return str(f), 500


@bp.route('/<int:wordlist_id>/contents', methods=['PUT'])
def update_wordlist_contents(wordlist_id):
    try:
        payload = request.get_json()
        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_CONTENTS_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    update_args = {}

    if 'notes' in payload:
        notes = payload.get('notes')
        update_args['notes'] = notes

    word_ids = None
    if 'word_ids' in payload:
        word_ids = payload.get('word_ids')

    unknown_word_ids = check_word_ids(word_ids)
    if unknown_word_ids:
        message = "unknown_word_ids:  %s" % unknown_word_ids
        return message, 400

    wordlist = __get_wordlist(wordlist_id)
    if wordlist['list_type'] == 'smart' and word_ids:
        return "can't add words to smart list", 400

    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            if update_args:
                update_args['wordlist_id'] = wordlist_id

                keez = ['notes']
                clauses = []
                for k in keez:
                    if k in update_args:
                        clauses.append('`%(key)s` = %%(%(key)s)s' % {'key': k})

                sql = """
                update wordlist
                set %(clauses)s
                where id = %%(wordlist_id)s
                """ % {'clauses': ', '.join(clauses)}

                cursor.execute(sql, update_args)

            if word_ids:
                wkw_tuples = [(wordlist_id, x) for x in word_ids]
                ins_sql = """
                insert ignore into wordlist_word (wordlist_id, word_id)
                values (%s, %s)
                """
                cursor.executemany(ins_sql, wkw_tuples)

            cursor.execute('commit')

            return __get_wordlist(wordlist_id)
        except Exception as e:
            cursor.execute('rollback')
            return "update list failed", 500


@bp.route('/<int:wordlist_id>', methods=['DELETE'])
def delete_wordlist(wordlist_id):
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "delete from wordlist where id = %s"
            cursor.execute(sql, (wordlist_id,))
            cursor.execute('commit')
            return "OK"
        except Exception as e:
            cursor.execute('rollback')
            return "delete list failed", 500


@bp.route('/<int:wordlist_id>/batch_delete', methods=['POST'])
def delete_from_wordlist(wordlist_id):
    try:
        payload = request.get_json()  # comes in as an array of ints, not a dict.
        jsonschema.validate(payload, dlernen_json_schema.WORDLIST_DELETE_WORDS_PAYLOAD_SCHEMA)
    except jsonschema.ValidationError as e:
        return "bad payload: %s" % e.message, 400

    # batch delete from wordlist; can remove both known and unknown words.
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        try:
            cursor.execute('start transaction')
            sql = "select sqlcode from wordlist where id = %s"
            cursor.execute(sql, (wordlist_id,))
            row = cursor.fetchone()
            if row and row['sqlcode']:
                cursor.execute('rollback')
                return "can't delete words from smart list", 400

            word_ids = payload.get('word_ids', [])

            # TODO - if a word_id is not in the wordlist, no harm done.  but to be thorough, we should
            #   check for this and return a 404.

            if word_ids:
                # note:  any tags that exist for this word in this wordlist will be automatically removed.
                # the foreign keys in the tag table point to wordlist_word, so no code needed for this.
                sql = """
                delete from wordlist_word 
                where wordlist_id = %(wordlist_id)s and word_id = %(word_id)s
                """
                args = [
                    {
                        "wordlist_id": wordlist_id,
                        "word_id": word_id
                    }
                    for word_id in word_ids
                ]
                cursor.executemany(sql, args)

            cursor.execute('commit')
            return "OK"
        except Exception as e:
            cursor.execute('rollback')
            return str(e), 500


@bp.route('/word_ids')
def get_word_ids_from_wordlists():
    # returns a list of the ids of the words in the given wordlists.  returns all the word ids
    # in the dictionary if no wordlist ids are given.  the list will not have dups.

    wordlist_ids = list(set(request.args.getlist('wordlist_id')))
    tags = list(set(request.args.getlist('tag')))

    # not going to bother checking whether the wordlist_ids or tags exist.  i'm tired.
    
    with closing(connect(**current_app.config['DSN'])) as dbh, closing(dbh.cursor(dictionary=True)) as cursor:
        if tags:
            if not wordlist_ids or len(wordlist_ids) != 1:
                return "need exactly one wordlist id when searching by tags", 400

            arglist = ['%s'] * len(tags)
            arglist = ', '.join(arglist)
            sql = """
            select distinct word_id
            from tag
            where wordlist_id = %%s
            and tag in (%(arglist)s)
            """ % {'arglist': arglist}

            args = [wordlist_ids[0]] + tags
            cursor.execute(sql, args)

            rows = cursor.fetchall()
            return {'word_ids': [x['word_id'] for x in rows]}

        if wordlist_ids:
            word_ids = common.get_word_ids_from_wordlists(wordlist_ids, cursor)

            return {'word_ids': word_ids}

        sql = """
        select id AS word_id
        from word
        """

        cursor.execute(sql)

        rows = cursor.fetchall()
        return {'word_ids': [x['word_id'] for x in rows]}
