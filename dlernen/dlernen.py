from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, current_app
from pprint import pprint
import requests
import json
from dlernen import dlernen_json_schema as js

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


@bp.errorhandler(500)
def server_error(e):
    return render_template('500.html', message=str(e), ), 500


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/lookup/<int:word_id>', methods=['GET'])
def lookup_by_get(word_id):
    # for when a word appears as a hyperlink in a page.
    return_to_wordlist_id = request.args.get('return_to_wordlist_id')

    # FIXME - gracefully handle status code <> 200

    r = requests.get(url_for('api_word.get_word_by_id', word_id=word_id, _external=True))
    result = r.json()

    r = requests.get(url_for('api_wordlist.get_wordlists_by_word_id', word_id=word_id, _external=True))
    member_wordlists = r.json()

    template_args = [(result, member_wordlists)]

    return render_template('lookup.html',
                           word=result["word"],
                           return_to_wordlist_id=return_to_wordlist_id,
                           template_args=template_args)


@bp.route('/lookup', methods=['POST'])
def lookup_by_post():
    # for looking up a word entered into a form.
    word = request.form.get('lookup')
    return_to_wordlist_id = request.form.get('return_to_wordlist_id')
    results = []
    r = requests.get(url_for('api_word.get_word', word=word, _external=True))
    if r.status_code == 404:
        pass
    elif r.status_code == 200:
        results = r.json()

    # if nothing found, redo the query as a partial match.
    if not results:
        r = requests.get(url_for('api_word.get_word', word=word, partial=True, _external=True))
        if r.status_code == 404:
            pass
        elif r.status_code == 200:
            results = r.json()

    results = sorted(results, key=lambda x: str.lower(x['word']))
    template_args = []
    for result in results:
        # FIXME - gracefully handle status code <> 200
        r = requests.get(url_for('api_wordlist.get_wordlists_by_word_id', word_id=result['word_id'], _external=True))
        member_wordlists = r.json()
        template_args.append((result, member_wordlists))

    return render_template('lookup.html',
                           word=word,
                           return_to_wordlist_id=return_to_wordlist_id,
                           template_args=template_args)


@bp.route('/wordlists')
def wordlists():
    url = url_for('api_wordlist.get_wordlists', _external=True)
    r = requests.get(url)
    if r:
        result = json.loads(r.text)
        return render_template('wordlists.html', rows=result)

    abort(r.status_code)


@bp.route('/list_attributes/<int:wordlist_id>')
def list_attributes(wordlist_id):
    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
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
    r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True))
    if r.status_code == 404:
        flash("wordlist %s not found" % wordlist_id)
        return redirect('/wordlists')

    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        r = requests.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
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
        return redirect(url_for('dlernen.wordlists'))

    if citation is not None:
        x = citation.strip()
        if not x:
            citation = None

    payload = {
        'name': name,
        'citation': citation
    }

    url = url_for('api_wordlist.create_wordlist_metadata', _external=True)
    r = requests.post(url, json=payload)
    if r.status_code == 200:
        return redirect(url_for('dlernen.wordlists'))

    raise Exception("something went wrong in POST: to %s - %s [%s]" % (url, r.text, r.status_code))


@bp.route('/deletelist', methods=['POST'])
def deletelist():
    doomed = request.form.getlist('deletelist')
    payload = {
        'deletelist': doomed
    }

    r = requests.delete(url_for('api_wordlist.delete_wordlists', _external=True), data=payload)
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

    url = url_for('api_wordlist.update_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
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
    url = url_for('api_word.get_word', word=word, _external=True)
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
        flash("""
        could not deal with word "%s" [%s]:  %s
        """ % (word, r.status_code, r.text))
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)
    if r.status_code != 200:
        flash(r.text)
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@bp.route('/update_notes', methods=['POST'])
def update_notes():
    payload = {
        'notes': request.form['notes']
    }
    wordlist_id = request.form['wordlist_id']

    url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id, _external=True)
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
        url = url_for('api_wordlist.delete_from_wordlist_by_id', wordlist_id=wordlist_id, word_id=word_id,
                      _external=True)
        r = requests.delete(url)

    for word in unknown_deleting:
        url = url_for('api_wordlist.delete_from_wordlist_by_word', wordlist_id=wordlist_id, word=word,
                      _external=True)
        r = requests.delete(url)

    # TODO - change API to allow batch delete.  we could do this with a single request

    target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@bp.route('/word/<string:word>')
def edit_word_form(word):
    wordlist_id = request.args.get('wordlist_id')

    url = url_for('api_misc.get_pos', word=word, _external=True)
    r = requests.get(url)
    pos_structure = r.json()

    # construct the field names for all the attributes.  field name formats are described in addword.html.
    form_data = {}

    # field_values_before is a mapping of field names to field values.  when the form is submitted,
    # we will get another such mapping, with whatever changes were made.  we implement the dictionary
    # update by diffing these and making the appropriate changes to the database.

    field_values_before = {}

    for p in pos_structure:

        if p['pos_name'] not in form_data:
            form_data[p['pos_name']] = []
        for a in p['attributes']:
            t = [p['pos_id'], a['attribute_id']]
            if p['word_id']:
                t.append(p['word_id'])
                if a['attrvalue_id']:
                    t.append(a['attrvalue_id'])
            t = list(map(str, t))  # convert to str so join won't choke
            field_name = '-'.join(t)
            field_value = a['attrvalue'] if a['attrvalue'] else ""
            d = {
                'field_name': field_name,
                'field_value': field_value,
                'label': a['attrkey'],
                'sort_order': a['sort_order']
            }
            form_data[p['pos_name']].append(d)
            field_values_before[field_name] = field_value
        form_data[p['pos_name']] = sorted(form_data[p['pos_name']], key=lambda x: x['sort_order'])

    if r:
        return render_template('addword.html',
                               word=word,
                               wordlist_id=wordlist_id,
                               return_to_wordlist_id=wordlist_id,
                               form_data=form_data,
                               field_values_before=json.dumps(field_values_before))

    abort(r.status_code)


@bp.route('/update_dict', methods=['POST'])
def update_dict():
    word = request.form.get('word', '').strip()
    word_before = request.form.get('word_before')
    wordlist_id = request.form.get('wordlist_id')
    field_values_before = json.loads(request.form.get('field_values_before'))
    field_values_after = {}
    for k in field_values_before.keys():
        field_values_after[k] = request.form.get(k)

    # go through all the attribute values and diff before/after.  we will construct add/update
    # payloads and send them off to the API.  we will have to construct one request per
    # word added/modified until i get around to batching it all in a single request.

    # we have to construct payloads for each (word, pos_id) that has changes.
    # make a dict mapping these tuples to payload objects.  also track whether
    # (word, pos_id) is associated with a word id.  if not, then we are adding.

    word_payloads = {}
    word_pos_to_word_id = {}

    for k in field_values_before.keys():
        value_before_unstripped = field_values_before[k]
        value_after_unstripped = field_values_after[k]
        value_before_stripped = value_before_unstripped.strip()
        value_after_stripped = value_after_unstripped.strip()

        ids = k.split('-')
        pos_id = int(ids[0])
        attribute_id = int(ids[1])
        word_id = str(ids[2]) if len(ids) > 2 else None
        attrvalue_id = str(ids[3]) if len(ids) > 3 else None

        t = (word, pos_id)
        if t not in word_payloads:
            word_payloads[t] = {}

        payload = word_payloads[t]
        if word_id:
            word_pos_to_word_id[t] = word_id

        if value_before_stripped and not value_after_stripped:
            # we are deleting the attribute value.
            # we will have a word_id and an attrvalue_id in this case
            if js.ATTRIBUTES_DELETING not in payload:
                payload[js.ATTRIBUTES_DELETING] = []
            payload[js.ATTRIBUTES_DELETING].append(int(attrvalue_id))
        elif value_after_stripped and not value_before_stripped:
            # we are adding a new attribute value.
            # we *might* have a word_id
            if js.ATTRIBUTES_ADDING not in payload:
                payload[js.ATTRIBUTES_ADDING] = []
            payload[js.ATTRIBUTES_ADDING].append({'attrvalue': value_after_unstripped,
                                                  'attribute_id': attribute_id})
            if word_id:
                word_pos_to_word_id[t] = word_id
        elif value_after_stripped != value_before_stripped:
            # we are changing an existing value.
            # we will have a word_id and an attrvalue_id
            if js.ATTRIBUTES_UPDATING not in payload:
                payload[js.ATTRIBUTES_UPDATING] = []
            payload[js.ATTRIBUTES_UPDATING].append({'attrvalue_id': int(attrvalue_id),
                                                    'attrvalue': value_after_unstripped})
        else:
            # stripped values are unchanged, but it may happen that the unstripped values are different
            # because we added/removed leading/trailing whitespace and did nothing else.
            if value_after_stripped and (value_before_unstripped != value_after_unstripped):
                if js.ATTRIBUTES_UPDATING not in payload:
                    payload[js.ATTRIBUTES_UPDATING] = []
                payload[js.ATTRIBUTES_UPDATING].append({'attrvalue_id': int(attrvalue_id),
                                                        'attrvalue': value_after_unstripped})

    # did we change the spelling of the word?  if so add new spelling to all the payloads.
    # the update request will take care of proper capitalization.
    if word and word != word_before:
        for k in word_payloads.keys():
            word_payloads[k]['word'] = word

    # go through the payloads and insert word and pos_name in payloads that we are POSTing.
    for k in word_payloads.keys():
        if not word_payloads[k]:
            continue

        if k not in word_pos_to_word_id:
            word_payloads[k]['word'] = word
            word_payloads[k]['pos_id'] = k[1]

    # get rid of empty payloads
    word_payloads = {key: value for key, value in word_payloads.items() if value}

    refresh_needed = False
    for k, payload in word_payloads.items():
        if k in word_pos_to_word_id:
            # we are updating
            word_id = word_pos_to_word_id[k]
            url = url_for('api_word.update_word', word_id=word_id, _external=True)
            r = requests.put(url, json=payload)
            if r.status_code != 200:
                flash("could not update word %s [%s]:  %s" % (word, r.status_code, r.text))
        else:
            # we are adding a new word
            url = url_for('api_word.add_word', _external=True)
            r = requests.post(url, json=payload)
            if r.status_code != 200:
                flash("could not insert word %s [%s]:  %s" % (word, r.status_code, r.text))
            else:
                refresh_needed = True

    if refresh_needed:
        refresh_payload = {
            'word': word,
        }
        url = url_for('api_wordlist.refresh_wordlists', _external=True)
        r = requests.put(url, json=refresh_payload)
        if r.status_code != 200:
            raise Exception("failed to refresh word lists")

    if wordlist_id:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    else:
        # if we didn't add a word to any list, return to the editing form for this word.
        target = url_for('dlernen.edit_word_form', word=word)

    return redirect(target)
