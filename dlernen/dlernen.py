from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, current_app
from pprint import pprint
import requests
import json

bp = Blueprint('dlernen', __name__)


def chunkify(arr, **kwargs):
    if not arr:
        return []

    nchunks = kwargs.get('nchunks')
    chunksize = kwargs.get('chunksize')
    if not nchunks and not chunksize:
        # return the whole array as one chunk
        return [arr]

    if nchunks and chunksize:
        raise Exception('set chunksize or nchunks but not both')

    arraysize = len(arr)
    if nchunks:
        # round up array size to nearest multiple of nchunks
        arraysize = ((arraysize + nchunks - 1) // nchunks) * nchunks
        chunksize = arraysize // nchunks

    # add one more increment of chunksize so that our zip array includes
    # the last elements
    chunks = [x for x in range(0, arraysize + chunksize, chunksize)]

    z = list(zip(chunks, chunks[1:]))

    result = []
    for x in z:
        result.append(arr[x[0]:x[1]])
    return result


@bp.route('/api/post_test', methods=['POST'])
def post_test():
    """
    apparently you can't use requests to send true JSON objects in a post request.  i.e. this did not work:

    IDS = [1, 2, 3, 4, 5]
    DATA = {
        "key": "value",
        "arr": IDS,     <== this is valid json but only the first item in the array is sent.
        "a": "aoeu"
    }

    but this did:

    IDS = [1, 2, 3, 4, 5]
    DATA = {
        "key": "value",
        "arr": json.dumps(IDS),  <== have to stringify the array before sending it over.
        "a": "aoeu"
    }
    """

    j = request.get_json()
    pprint(j)
    return j


# TODO - delete an attrkey value - /api/<word_id>/attrkey/<attrvalue_id>


@bp.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


@bp.route('/')
def home():
    return render_template('home.html')


def get_lookup_render_template(word, **kwargs):
    return_to_wordlist_id = kwargs.get('return_to_wordlist_id')
    member_wordlists = kwargs.get('member_wordlists')
    url = "%s/api/word/%s" % (current_app.config['DB_URL'], word)
    results = None
    r = requests.get(url)
    if r.status_code == 404:
        pass
    elif r.status_code == 200:
        results = r.json()
    return render_template('lookup.html',
                           word=word,
                           return_to_wordlist_id=return_to_wordlist_id,
                           member_wordlists=member_wordlists,
                           results=results)


@bp.route('/lookup/<string:word>', methods=['GET'])
def lookup_by_get(word):
    return_to_wordlist_id = request.args.get('return_to_wordlist_id')
    word_id = request.args.get('word_id')
    member_wordlists = None
    if word_id:
        url = "%s/api/wordlists/%s" % (current_app.config['DB_URL'], word_id)
        r = requests.get(url)
        member_wordlists = r.json()
    return get_lookup_render_template(word, return_to_wordlist_id=return_to_wordlist_id,
                                      member_wordlists=member_wordlists)


# TODO - see if we really need this.
@bp.route('/lookup', methods=['POST'])
def lookup_by_post():
    word = request.form.get('lookup')
    return_to_wordlist_id = request.form.get('return_to_wordlist_id')
    return get_lookup_render_template(word, return_to_wordlist_id=return_to_wordlist_id)


@bp.route('/wordlists')
def wordlists():
    url = "%s/api/wordlists" % current_app.config['DB_URL']
    r = requests.get(url)
    if r:
        result = json.loads(r.text)
        return render_template('wordlists.html', rows=result)

    abort(r.status_code)


@bp.route('/list_attributes/<int:wordlist_id>')
def list_attributes(wordlist_id):
    url = "%s/api/wordlist/%s/metadata" % (current_app.config['DB_URL'], wordlist_id)
    r = requests.get(url)
    if r:
        result = r.json()
        if result['sqlcode'] is None:
            result['sqlcode'] = ''
        if result['citation'] is None:
            result['citation'] = ''
        return render_template('list_attributes.html',
                               wordlist=result,
                               return_to_wordlist_id=wordlist_id)

    abort(r.status_code)


@bp.route('/wordlist/<int:wordlist_id>')
def wordlist(wordlist_id):
    nchunks = request.args.get('nchunks', current_app.config['NCHUNKS'], type=int)
    url = "%s/api/wordlist/%s" % (current_app.config['DB_URL'], wordlist_id)
    r = requests.get(url)
    if r.status_code == 404:
        flash("wordlist %s not found" % wordlist_id)
        return redirect('/wordlists')

    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        url = "%s/api/wordlist/%s/metadata" % (current_app.config['DB_URL'], wordlist_id)
        r = requests.get(url)
        result = r.json()
        if result['sqlcode'] is None:
            result['sqlcode'] = ''
        if result['citation'] is None:
            result['citation'] = ''
        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               wordlist=result,
                               return_to_wordlist_id=wordlist_id)

    result = r.json()
    if result['notes'] is None:
        # otherwise the word 'None' is rendered in the form
        result['notes'] = ''

    if result['list_type'] == 'smart':
        words = chunkify(result['known_words'], nchunks=nchunks)
        return render_template('smart_wordlist.html',
                               result=result,
                               words=words)

    known_words = chunkify(result['known_words'], nchunks=nchunks)
    unknown_words = chunkify(result['unknown_words'], nchunks=nchunks)

    return render_template('wordlist.html',
                           result=result,
                           known_words=known_words,
                           unknown_words=unknown_words)


@bp.route('/addlist', methods=['POST'])
def addlist():
    # note that the values in the form have not been subject to json schema validation.  these are just
    # whatever bullshit was entered into the form.  so we have to fiddle with the values before stuffing
    # them into the payload, which IS validated.

    name = request.form.get('name')
    citation = request.form.get('citation')

    if name:
        name = name.strip()

    if not name:
        flash("Die Liste muss einen Namen haben")
        return redirect('/wordlists')

    if citation is not None:
        x = citation.strip()
        if not x:
            citation = None

    payload = {
        'name': name,
        'citation': citation
    }

    url = "%s/api/wordlist/metadata" % current_app.config['DB_URL']
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        return redirect('/wordlists')

    raise Exception("something went wrong in POST: to %s - %s [%s]" % (url, r.text, r.status_code))


@bp.route('/deletelist', methods=['POST'])
def deletelist():
    doomed = request.form.getlist('deletelist')
    url = "%s/api/wordlists" % current_app.config['DB_URL']
    payload = {
        'deletelist': doomed
    }

    r = requests.delete(url, data=payload)
    if r.status_code == 200:
        return redirect('/wordlists')
    raise Exception("something went wrong in /api/wordlists: %s" % r.text)


@bp.route('/edit_list_attributes', methods=['POST'])
def edit_list_attributes():
    # note that the values in the form have not been subject to json schema validation.  these are just
    # whatever bullshit was entered into the form (the list_attributes template).  so we have to
    # fiddle with the values before stuffing them into the payload, which IS validated.

    name = request.form.get('name')
    citation = request.form.get('citation')
    sqlcode = request.form.get('sqlcode')
    wordlist_id = request.form.get('wordlist_id')

    if name:
        name = name.strip()

    if not name:
        flash("Die Liste muss einen Namen haben")
        result = {
            "sqlcode": '' if sqlcode is None else sqlcode,
            "citation": '' if citation is None else citation,
            "wordlist_id": wordlist_id
        }
        return render_template('list_attributes.html',
                               wordlist=result,
                               return_to_wordlist_id=wordlist_id)

    if sqlcode is not None:
        x = sqlcode.strip()
        if not x:
            sqlcode = None

    if citation is not None:
        x = citation.strip()
        if not x:
            citation = None

    payload = {
        'name': name,
        'sqlcode': sqlcode,
        'citation': citation
    }

    url = "%s/api/wordlist/%s/metadata" % (current_app.config['DB_URL'], wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code == 200:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        return redirect(target)
    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        payload = {
            'name': name,
            'citation': '' if citation is None else citation,
            'sqlcode': sqlcode,
            'wordlist_id': wordlist_id
        }
        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               wordlist=payload,
                               return_to_wordlist_id=wordlist_id)
    raise Exception("something went wrong in %s PUT: %s (%s)" % (url, r.text, r.status_code))


# TODO if this is for a POST request, why does it call requests.put()?
@bp.route('/add_to_list', methods=['POST'])
def add_to_list():
    word = request.form['word'].strip()
    wordlist_id = request.form['wordlist_id']

    # TODO - for now, we can only add a word to a wordlist, not a word_id.
    payload = None
    url = "%s/api/word/%s" % (current_app.config['DB_URL'], word)
    r = requests.get(url)
    if r.status_code == 404:
        payload = {
            "words": [
                word
            ]
        }
    elif r.status_code == 200:
        payload = {
            "words": [
                word
            ]
        }

    if not payload:
        raise Exception("add_to_list could not make payload")

    url = "%s/api/wordlist/%s/contents" % (current_app.config['DB_URL'], wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code != 200:
        raise Exception("well, shit")

    target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@bp.route('/update_notes', methods=['POST'])
def update_notes():
    payload = {
        'notes': request.form['notes']
    }
    wordlist_id = request.form['wordlist_id']

    url = "%s/api/wordlist/%s/contents" % (current_app.config['DB_URL'], wordlist_id)
    r = requests.put(url, json=payload)
    if r.status_code == 200:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    raise Exception("something went wrong in /api/wordlist PUT: %s" % r.text)


@bp.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    wordlist_id = request.form['wordlist_id']
    known_deleting = request.form.getlist('known_wordlist')
    unknown_deleting = request.form.getlist('unknown_wordlist')

    for word_id in known_deleting:
        url = "%s/api/wordlist/%s/%s" % (current_app.config['DB_URL'], wordlist_id, int(word_id))
        r = requests.delete(url)

    for word in unknown_deleting:
        url = "%s/api/wordlist/%s/%s" % (current_app.config['DB_URL'], wordlist_id, word)
        r = requests.delete(url)

    # TODO - change API to allow batch delete.  we could do this with a single request

    target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@bp.route('/word/<string:word>')
def edit_word_form(word):
    wordlist_id = request.args.get('wordlist_id')

    url = "%s/api/word/metadata?word=%s" % (current_app.config['BASE_URL'], word)
    r = requests.get(url)
    if r:
        pos_infos = r.json()
        return render_template('addword.html',
                               word=word,
                               wordlist_id=wordlist_id,
                               return_to_wordlist_id=wordlist_id,
                               pos_infos=pos_infos)

    abort(r.status_code)


@bp.route('/update_dict', methods=['POST'])
def update_dict():
    tag = request.form.get('tag')
    if not tag:
        word = request.form.get('word')
        wordlist_id = request.form.get('wordlist_id')
        if word is not None:
            flash("Select a Part of Speech")
            return redirect(url_for('dlernen.edit_word_form', word=word, wordlist_id=wordlist_id))

        raise Exception("select a part of speech")

    # tag is <pos_id>-<pos_name>-<word_id> for the editing case and <pos_id>-<pos_name> for the adding case.

    tag_parts = tag.split('-')
    pos_id = tag_parts[0]
    word_id = None
    if len(tag_parts) > 2:
        word_id = tag_parts[2]

    # get all the attrkey info from the form and turn it into a dict.
    attrs_from_form = {}
    for f in request.form.keys():
        field_key_parts = f.split('-')
        p = field_key_parts[0]
        if p != pos_id:
            continue
        attrkey = field_key_parts[1]
        if attrkey not in attrs_from_form:
            attrs_from_form[attrkey] = {}
            attrvalue = request.form.get(f)
            if attrvalue:
                attrs_from_form[attrkey]['attrvalue'] = attrvalue
            if len(field_key_parts) > 2:
                attrs_from_form[attrkey]['attrvalue_id'] = int(field_key_parts[2])

    if not word_id:
        pos_name = tag_parts[1]
        word = request.form.get('word')
        if word is not None:
            word = word.strip()
        if not word:
            raise Exception('word for add_word is empty')
        payload = {
            'word': word,
            'pos_name': pos_name,
            'attributes': []
        }

        for k in attrs_from_form.keys():
            attrvalue = attrs_from_form[k].get('attrvalue')
            if attrvalue:
                payload['attributes'].append(
                    {
                        'attrkey': k,
                        'attrvalue': attrvalue
                    }
                )

        url = "%s/api/word" % current_app.config['DB_URL']
        r = requests.post(url, json=payload)
        if r.status_code != 200:
            raise Exception("failed to insert word '%s'" % word)

        obj = r.json()

        # remove this word from the unknown wordlists and put the word_id into the known words for those lists.

        refresh_payload = {
            'word': word,
            'word_id': obj['word_id']
        }
        url = "%s/api/wordlists" % current_app.config['DB_URL']
        r = requests.put(url, json=refresh_payload)
        if r.status_code != 200:
            raise Exception("failed to refresh word lists")

        wordlist_id = request.form.get('wordlist_id')
        if wordlist_id:
            target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        else:
            # if we didn't add a word to any list, return to the editing form for this word.
            target = url_for('dlernen.edit_word_form', word=word)

        return redirect(target)

    # we are updating.  figure out all the attrkey values we have to add/remove/update.

    # go through the contents of the form and figure out what changes to make.  cases:
    #
    # 1.  if there is an attrvalue_id but no value, we are deleting.
    # 2.  if there is an attrvalue but no attrvalue id, we are adding.
    # 3.  if both are present, we are updating.

    payload = {
        "attributes_adding": [],
        "attributes_deleting": [],
        "attributes_updating": []
    }

    word = request.form.get('word')
    if word is not None:
        word = word.strip()
    if word:
        payload['word'] = word.strip()

    for k, v in attrs_from_form.items():
        if 'attrvalue' not in v and 'attrvalue_id' in v:
            payload["attributes_deleting"].append(int(v['attrvalue_id']))
        elif 'attrvalue_id' not in v and 'attrvalue' in v:
            payload["attributes_adding"].append(
                {
                    'attrkey': k,
                    'attrvalue': v['attrvalue']
                }
            )
        elif v:
            payload['attributes_updating'].append(v)

    url = "%s/api/word/%s" % (current_app.config['DB_URL'], word_id)
    r = requests.put(url, json=payload)

    wordlist_id = request.form.get('wordlist_id')
    if wordlist_id:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    else:
        # if we didn't add a word to any list, return to the editing form for this word.
        target = url_for('dlernen.edit_word_form', word=word)

    return redirect(target)
