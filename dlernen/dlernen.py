from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, current_app
from pprint import pprint
import requests
import json
from dlernen import dlernen_json_schema as js

bp = Blueprint('dlernen', __name__)


def chunkify(arr, **kwargs):
    if not arr:
        return []

    nchunks = kwargs.get('nchunks', 1)
    nchunks = max(nchunks, 1)

    # round up array size to nearest multiple of nchunks
    arraysize = ((len(arr) + nchunks - 1) // nchunks) * nchunks
    chunksize = arraysize // nchunks

    # add one more increment of chunksize so that our zip array includes
    # the last elements
    chunks = [x for x in range(0, arraysize + chunksize, chunksize)]

    z = list(zip(chunks, chunks[1:]))

    result = []
    for x in z:
        result.append(arr[x[0]:x[1]])
    return result


@bp.route('/')
def home():
    return render_template('home.html')


@bp.route('/lookup/<int:word_id>', methods=['GET'])
def lookup_by_get(word_id):
    # for when a word appears as a hyperlink in a page.
    return_to_wordlist_id = request.args.get('return_to_wordlist_id')

    r = requests.get(url_for('api_word.get_word_by_id', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    result = r.json()

    r = requests.get(url_for('api_wordlist.get_wordlists_by_word_id', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

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
    r = requests.get(url_for('api_word.get_word', word=word, partial=True, _external=True))
    if r.status_code == 404:
        pass
    elif r.status_code == 200:
        results = r.json()
    else:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    # # if nothing found, redo the query as a partial match.
    # if not results:
    #     r = requests.get(url_for('api_word.get_word', word=word, partial=True, _external=True))
    #     if r.status_code == 404:
    #         pass
    #     elif r.status_code == 200:
    #         results = r.json()
    #     else:
    #         return render_template("error.html",
    #                                message=r.text,
    #                                status_code=r.status_code)

    results = sorted(results, key=lambda x: str.lower(x['word']))
    template_args = []
    for result in results:
        r = requests.get(url_for('api_wordlist.get_wordlists_by_word_id', word_id=result['word_id'], _external=True))
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

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

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/list_attributes/<int:wordlist_id>')
def list_attributes(wordlist_id):
    url = url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_metadata = r.json()

    url = url_for('api_wordlist_tag.get_tags', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_tags = r.json()

    if wordlist_metadata['sqlcode'] is None:
        wordlist_metadata['sqlcode'] = ''
    if wordlist_metadata['citation'] is None:
        wordlist_metadata['citation'] = ''
    return render_template('list_attributes.html',
                           wordlist_metadata=wordlist_metadata,
                           wordlist_tags=wordlist_tags,
                           return_to_wordlist_id=wordlist_id)


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
                               wordlist_metadata=result,
                               return_to_wordlist_id=wordlist_id)

    if r:
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

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


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
    if r:
        return redirect(url_for('dlernen.wordlists'))

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/deletelist', methods=['POST'])
def deletelist():
    doomed = request.form.getlist('deletelist')
    doomed = list(map(int, doomed))

    r = requests.put(url_for('api_wordlist.delete_wordlists', _external=True), json=doomed)
    if r:
        return redirect('/wordlists')

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/edit_list_attributes', methods=['POST'])
def edit_list_attributes():
    # note that the values in the form have not been subject to json schema validation.  these are just
    # whatever bullshit was entered into the form (the list_attributes template).  so we have to
    # fiddle with the values before stuffing them into the payload, which IS validated.

    name = request.form.get('name')
    citation = request.form.get('citation')
    sqlcode = request.form.get('sqlcode')
    wordlist_id = request.form.get('wordlist_id')
    new_tags = request.form.get('add_tags', '')

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
                               wordlist_metadata=result,
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
                               wordlist_metadata=payload,
                               return_to_wordlist_id=wordlist_id)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    # #################### everything south of here deals with updating the tags

    # it may happen that the same tag is given for add and update.  i.e. we update a tag
    # to the same name as one we are adding.  the update wins and the one being added should be ignored.
    # which means we process the updates first and then the adds.

    # the field names of the tag edit fields are 'tag-<tag_id>'.  do this to get the tag ids
    # and the values passed in to the form.
    r = requests.get(url_for('api_wordlist_tag.get_tags', wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_tags = r.json()
    update_payload = []
    for t in wordlist_tags['tags']:
        field_name = "tag-%s" % t['tag_id']
        new_value = request.form.get(field_name, '').strip()
        d = {
            "tag_id": t['tag_id']
        }
        if new_value:
            d['tag'] = new_value
        update_payload.append(d)

    if update_payload:
        r = requests.put(url_for('api_wordlist_tag.update_tags', wordlist_id=wordlist_id, _external=True),
                         json=update_payload)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

    tags = new_tags.split(',')
    tags = [x.strip() for x in tags]
    tags = list(filter(lambda x: bool(x), tags))  # filter out empty strings

    r = requests.post(url_for('api_wordlist_tag.add_tags', wordlist_id=wordlist_id, _external=True), json=tags)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    metadata = {
        'name': name,
        'citation': '' if citation is None else citation,
        'sqlcode': '' if sqlcode is None else sqlcode,
        'wordlist_id': wordlist_id
    }

    # refresh the tag info for display
    r = requests.get(url_for('api_wordlist_tag.get_tags', wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_tags = r.json()

    return render_template('list_attributes.html',
                           wordlist_metadata=metadata,
                           wordlist_tags=wordlist_tags,
                           return_to_wordlist_id=wordlist_id)


# TODO if this is for a POST request, why does it call requests.put()?
@bp.route('/add_to_list', methods=['POST'])
def add_to_list():
    # the get_word function will check that the word is not garbage, no need to do it here.
    word = request.form['word'].strip()
    wordlist_id = request.form['wordlist_id']

    # TODO - for now, we can only add a word to a wordlist, not a word_id.
    url = url_for('api_word.get_word', word=word, _external=True)
    r = requests.get(url)
    payload = None
    if r.status_code == 404 or r.status_code == 200:
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
    if not r:
        flash(r.text)

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
    if r:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
        return redirect(target)

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    wordlist_id = request.form['wordlist_id']
    known_deleting = request.form.getlist('known_wordlist')
    unknown_deleting = request.form.getlist('unknown_wordlist')

    for word_id in known_deleting:
        url = url_for('api_wordlist.delete_from_wordlist_by_id', wordlist_id=wordlist_id, word_id=word_id,
                      _external=True)
        r = requests.delete(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

    for word in unknown_deleting:
        url = url_for('api_wordlist.delete_from_wordlist_by_word', wordlist_id=wordlist_id, word=word,
                      _external=True)
        r = requests.delete(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

    # TODO - change API to allow batch delete.  we could do this with a single request

    target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    return redirect(target)


@bp.route('/word/<string:word>')
def edit_word_form(word):
    wordlist_id = request.args.get('wordlist_id')

    url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    pos_structure = r.json()

    # construct the field names for all the attributes.  field name formats are described in addword.html.
    form_data = {p['pos_name']: [] for p in pos_structure}

    # field_values_before is a mapping of field names to field values.  when the form is submitted,
    # we will get another such mapping, with whatever changes were made.  we implement the dictionary
    # update by diffing these and making the appropriate changes to the database.

    field_values_before = {}

    for p in pos_structure:
        for a in p['attributes']:
            t = [p['pos_id'], a['attribute_id']]
            if p['word_id']:
                t.append(p['word_id'])

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

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/update_dict', methods=['POST'])
def update_dict():
    word = request.form.get('word', '').strip()
    word_before = request.form.get('word_before')
    wordlist_id = request.form.get('wordlist_id')
    field_values_before = json.loads(request.form.get('field_values_before'))
    field_values_after = {k: request.form.get(k) for k in field_values_before.keys()}

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

        t = (word, pos_id)
        if t not in word_payloads:
            word_payloads[t] = {}

        payload = word_payloads[t]
        if word_id:
            word_pos_to_word_id[t] = int(word_id)

        if value_before_stripped and not value_after_stripped:
            # we are deleting the attribute value.
            # we will have a word_id in this case
            if js.ATTRIBUTES not in payload:
                payload[js.ATTRIBUTES] = []
            payload[js.ATTRIBUTES].append({'attribute_id': attribute_id})
        elif value_after_stripped and not value_before_stripped:
            # we are adding a new attribute value.
            # we *might* have a word_id
            if js.ATTRIBUTES not in payload:
                payload[js.ATTRIBUTES] = []
            payload[js.ATTRIBUTES].append({'attrvalue': value_after_unstripped,
                                           'attribute_id': attribute_id})
            # if word_id:
            #     word_pos_to_word_id[t] = word_id
        elif value_after_stripped != value_before_stripped:
            # we are changing an existing value.
            # we will have a word_id
            if js.ATTRIBUTES not in payload:
                payload[js.ATTRIBUTES] = []
            payload[js.ATTRIBUTES].append({'attribute_id': attribute_id,
                                           'attrvalue': value_after_unstripped})
        else:
            # stripped values are unchanged, but it may happen that the unstripped values are different
            # because we added/removed leading/trailing whitespace and did nothing else.
            if value_after_stripped and (value_before_unstripped != value_after_unstripped):
                if js.ATTRIBUTES not in payload:
                    payload[js.ATTRIBUTES] = []
                payload[js.ATTRIBUTES].append({'attribute_id': attribute_id,
                                               'attrvalue': value_after_unstripped})

    # did we change the spelling of the word?  if so add new spelling to all the payloads
    # for which word ids exist.
    # the update request will take care of proper capitalization.
    #
    # don't do any folding to compare before/after, just compare raw strings.  this will
    # mean that changing xxx to XXX looks like a spelling change, but the view function will deal with this.
    if word and word != word_before:
        for k in word_payloads.keys():
            if k in word_pos_to_word_id:
                word_payloads[k]['word'] = word

    # go through the payloads and insert word and pos_name in payloads that we are POSTing,
    # or word_id for those we are PUTting.
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
            if not r:
                flash("could not update word %s [%s]:  %s" % (word, r.status_code, r.text))
        else:
            # we are adding a new word
            url = url_for('api_word.add_word', _external=True)
            r = requests.post(url, json=payload)
            if r:
                refresh_needed = True
            else:
                flash("could not insert word %s [%s]:  %s" % (word, r.status_code, r.text))

    if refresh_needed:
        refresh_payload = {
            'word': word,
        }
        url = url_for('api_wordlist.refresh_wordlists', _external=True)
        r = requests.put(url, json=refresh_payload)
        if not r:
            return render_template("error.html",
                                   message="failed to refresh word lists:  %s" % r.text,
                                   status_code=r.status_code)

    if wordlist_id:
        target = url_for('dlernen.wordlist', wordlist_id=wordlist_id)
    else:
        # if we didn't add a word to any list, return to the editing form for this word.
        target = url_for('dlernen.edit_word_form', word=word)

    return redirect(target)


@bp.route('/quiz_report/<int:wordlist_id>')
def quiz_report(wordlist_id):
    url = url_for('api_quiz_v2.get_report', quiz_key='definitions', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    report = r.json()
    return render_template("quiz_report.html",
                           quiz_key=report['quiz_key'],
                           wordlist_name=report['wordlist_name'],
                           wordlist_id=report['wordlist_id'],
                           scores=report['scores'])