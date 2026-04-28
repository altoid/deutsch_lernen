from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
import requests
import json
from dlernen import dlernen_json_schema as js
from dlernen.tagstate import TagState

from pprint import pprint

bp = Blueprint('dlernen', __name__, url_prefix='/dlernen')


def chunkify(arr, nchunks=1):
    # subdivide the array into <nchunks> subarrays of equal length
    if not arr:
        return []

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


@bp.route('/word/<string:word>', methods=['GET'])
def lookup_word(word):
    partial_match = request.args.get('partial', 'false')
    serialized_tag_state = request.args.get('serialized_tag_state')
    partial = False
    if partial_match.lower() == 'true':
        partial = True

    results = []
    r = requests.get(url_for('api_word.get_word', word=word, partial=partial, _external=True))
    if r.status_code == 404:
        pass
    elif r.status_code == 200:
        results = r.json()
    else:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    words_found = {x['word'].casefold() for x in results}
    exact_match_found = word.casefold() in words_found

    matching_word_ids = [x['word_id'] for x in results]

    r = requests.get(url_for('api_word.get_member_wordlists_multiple', word_id=matching_word_ids, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    search_results = r.json()

    # get wordlist if appropriate
    if serialized_tag_state:
        # see which of the search results are already in the wordlist.
        tag_state = TagState.deserialize(serialized_tag_state)
        r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=tag_state.wordlist_id, _external=True))
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist_obj = r.json()
        member_word_ids = {x['word_id'] for x in wordlist_obj['words']}
        matching_member_word_ids = set(matching_word_ids) & member_word_ids

        word_ids_to_words = {x['word_id']: x for x in wordlist_obj['words']}
        # decorate the search result keys
        for r in search_results:
            if r['word']['word_id'] in matching_member_word_ids:
                r['word']['is_member'] = True
                r['word']['tags'] = ' '.join(word_ids_to_words[r['word']['word_id']]['tags'])
            else:
                r['word']['is_member'] = False

        return render_template('search_results.html',
                               word=word,
                               matching_word_ids=matching_word_ids,
                               exact_match_found=exact_match_found,
                               search_results=search_results,
                               tag_state=tag_state)

    return render_template('search_results.html',
                           word=word,
                           exact_match_found=exact_match_found,
                           search_results=search_results)


@bp.route('/word/<int:word_id>', methods=['GET'])
def lookup_by_id(word_id):
    # for when a word appears as a hyperlink in a page.
    wordlist_id = request.args.get('wordlist_id')

    r = requests.get(url_for('api_word.get_word_by_id', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordobject = r.json()

    r = requests.get(url_for('api_word.get_member_wordlists', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    obj = r.json()
    member_wordlists = obj['wordlist_metadata_list']

    r = requests.get(url_for('api_word.get_relations', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    relations = r.json()

    if wordlist_id:
        tag_state = TagState.deserialize(request.args.get('serialized_tag_state'))
        return render_template('lookup.html',
                               wordobject=wordobject,
                               member_wordlists=member_wordlists,
                               relations=relations,
                               tag_state=tag_state)

    return render_template('lookup.html',
                           wordobject=wordobject,
                           member_wordlists=member_wordlists,
                           relations=relations)


@bp.route('/lookup', methods=['POST'])
def lookup_by_post():
    # submitting from the search field in the sidebar will bring us here.
    #

    word = request.form.get('lookup')
    serialized_tag_state = request.form.get('serialized_tag_state')

    return redirect(url_for('dlernen.lookup_word',
                            word=word,
                            partial='true',
                            serialized_tag_state=serialized_tag_state))


@bp.route('/wordlists')
def wordlists():
    url = url_for('api_wordlist.get_metadata_multiple', _external=True)
    r = requests.get(url)
    if r:
        result = json.loads(r.text)
        return render_template('wordlists.html', rows=result)

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/list_attributes/<int:wordlist_id>')
def list_attributes(wordlist_id):
    url = url_for('api_wordlist.get_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)
    wordlist_metadata = {k: '' if v is None else v for k, v in r.json().items()}

    return render_template('list_attributes.html',
                           wordlist_metadata=wordlist_metadata,
                           tag_state=TagState.deserialize(request.args.get('serialized_tag_state')))


@bp.route('/list_editor/<int:wordlist_id>')
def list_editor(wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    if serialized_tag_state:
        tag_state = TagState.deserialize(serialized_tag_state)
    else:
        tag_state = TagState(wordlist_id)

    r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)
    wordlist_obj = r.json()

    return render_template('list_editor.html',
                           tag_state=tag_state,
                           wordlist=wordlist_obj)


@bp.route('/wordlist/update_tags/<int:wordlist_id>', methods=['POST'])
def update_tag_state(wordlist_id):
    # the checkboxes are all called "tag"
    tags = request.form.getlist('tag')

    tag_state_object = TagState.deserialize(request.form.get('serialized_tag_state'))

    tag_state_object.clear()
    tag_state_object.set_tags(tags)

    return redirect(url_for('dlernen.wordlist',
                            wordlist_id=wordlist_id,
                            serialized_tag_state=tag_state_object.serialize()))


@bp.route('/wordlist/<int:wordlist_id>')
def wordlist(wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    if serialized_tag_state:
        tag_state_object = TagState.deserialize(serialized_tag_state)
        tag_state_object.update()  # you never know
    else:
        tag_state_object = TagState(wordlist_id)

    r = requests.get(url_for('api_wordlist.get_wordlist',
                             tag=tag_state_object.selected_tags(),
                             wordlist_id=wordlist_id,
                             _external=True))
    if r.status_code == 404:
        flash("wordlist %s not found" % wordlist_id)
        return redirect('/wordlists')

    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        r2 = requests.get(url_for('api_wordlist.get_metadata', wordlist_id=wordlist_id, _external=True))
        wordlist_metadata = {k: '' if v is None else v for k, v in r2.json().items()}

        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               tag_state=TagState.deserialize(request.args.get('serialized_tag_state')),
                               wordlist_metadata=wordlist_metadata)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_obj = r.json()
    if wordlist_obj['notes'] is None:
        # otherwise the word 'None' is rendered in the form
        wordlist_obj['notes'] = ''

    nchunks = request.args.get('nchunks', current_app.config['NCHUNKS'], type=int)
    words = chunkify(wordlist_obj['words'], nchunks)
    tag_chunks = chunkify(tag_state_object.tag_state(), 4)

    r = requests.get(url_for('api_wordlist.get_relations',
                             wordlist_id=wordlist_id,
                             _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    relations = r.json()

    return render_template('wordlist.html',
                           wordlist=wordlist_obj,
                           relations=relations,
                           tag_state=tag_state_object,
                           tag_chunks=tag_chunks,
                           words=words)


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

    url = url_for('api_wordlist.create_wordlist', _external=True)
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
        return redirect(url_for('dlernen.wordlists'))

    return render_template("error.html",
                           message=r.text,
                           status_code=r.status_code)


@bp.route('/list_attributes', methods=['POST'])
def edit_list_attributes():
    # note that the values in the form have not been subject to json schema validation.  these are just
    # whatever bullshit was entered into the form (the list_attributes template).  so we have to
    # fiddle with the values before stuffing them into the payload, which IS validated.

    name = request.form.get('name', '')
    citation = request.form.get('citation', '')
    sqlcode = request.form.get('sqlcode', '')
    wordlist_id = request.form.get('wordlist_id')
    list_type = request.form.get('list_type')

    # snapshot the list metadata as entered into the form in case we need to render it again later.
    metadata = {
        "name": name,
        "sqlcode": sqlcode,
        "citation": citation,
        "wordlist_id": wordlist_id,
        "list_type": list_type,
    }

    name = name.strip()
    if not name:
        flash("Die Liste muss einen Namen haben")
        return render_template('list_attributes.html',
                               tag_state=TagState.deserialize(request.form.get('serialized_tag_state')),
                               wordlist_metadata=metadata)

    x = sqlcode.strip()
    if not x:
        sqlcode = None

    x = citation.strip()
    if not x:
        citation = None

    payload = {
        'name': name,
        'sqlcode': sqlcode,
        'citation': citation
    }

    url = url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)

    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               tag_state=TagState.deserialize(request.form.get('serialized_tag_state')),
                               wordlist_metadata=metadata)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    return redirect(url_for('dlernen.wordlist',
                            serialized_tag_state=request.form.get('serialized_tag_state'),
                            wordlist_id=wordlist_id))


@bp.route('/list_editor', methods=['POST'])
def edit_list_contents():
    wordlist_id = request.form.get('wordlist_id')
    button = request.form.get('submit')
    serialized_tag_state = request.form.get('serialized_tag_state')
    tag_state_object = TagState.deserialize(serialized_tag_state)

    if button.startswith("Delete"):
        # the checkboxes are called 'removing'

        word_ids = list(map(int, request.form.getlist('removing')))
        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.put(url, json={
            "word_ids": word_ids
        })
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

    elif button.startswith("Update"):
        # the text fields are all named 'tag-<word_id>'
        # the checkboxes for tags are all named 'untag-<word_id>-<tag>'

        # get the keys for the text fields.
        tag_textfield_keys = list(filter(lambda x: x.startswith('tag-'), request.form.keys()))
        payload = []

        for k in tag_textfield_keys:
            new_tags = request.form.get(k, '').strip().split()
            if not new_tags:
                continue
            _, word_id = k.split('-')
            word_id = int(word_id)
            payload.append(
                {
                    'word_id': word_id,
                    'tags': new_tags
                }
            )
        url = url_for('api_wordlist_tag.add_tags',
                      wordlist_id=wordlist_id,
                      _external=True)
        r = requests.post(url, json=payload)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

        # get the keys for the checkboxes
        untag_keys = list(filter(lambda x: x.startswith('untag-'), request.form.keys()))
        word_ids_to_tags = {}
        for k in untag_keys:
            _, word_id, tag = k.split('-')
            if word_id not in word_ids_to_tags:
                word_ids_to_tags[word_id] = []
            word_ids_to_tags[word_id].append(tag)

        for word_id, tags in word_ids_to_tags.items():
            url = url_for('api_wordlist_tag.delete_tags_for_word_id',
                          wordlist_id=wordlist_id,
                          word_id=word_id,
                          tag=tags,
                          _external=True)
            r = requests.delete(url)
            if not r:
                return render_template("error.html",
                                       message=r.text,
                                       status_code=r.status_code)

    tag_state_object.update()
    serialized_tag_state = tag_state_object.serialize()

    return redirect(url_for('dlernen.list_editor',
                            serialized_tag_state=serialized_tag_state,
                            wordlist_id=wordlist_id,
                            _external=True))


@bp.route('/update_wordlist_notes', methods=['POST'])
def update_wordlist_notes():
    wordlist_id = request.form['wordlist_id']

    payload = {
        'notes': request.form['notes']
    }

    url = url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    target = url_for('dlernen.wordlist',
                     wordlist_id=wordlist_id,
                     serialized_tag_state=request.form.get('serialized_tag_state'))

    return redirect(target)


@bp.route('/update_word_notes', methods=['POST'])
def update_word_notes():
    word_id = request.form.get('word_id')
    wordlist_id = request.form.get('wordlist_id')
    serialized_tag_state = request.form.get('serialized_tag_state')

    notes = request.form.get('notes')
    if not notes.strip():
        notes = None

    payload = {
        "notes": notes
    }

    r = requests.put(url_for('api_word.update_word', word_id=word_id, _external=True), json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    target = url_for('dlernen.lookup_by_id',
                     word_id=word_id,
                     serialized_tag_state=serialized_tag_state,
                     wordlist_id=wordlist_id)

    return redirect(target)


@bp.route('/word_editor/<string:word>', methods=['GET'])
def edit_word_form(word):
    # construct the editing form for this word, with all attributes for all parts of speech.
    # field name formats are described in word_editor.html.  a tags field
    # will NOT appear for the part of speech if:
    #
    # - no wordlist_id is present OR
    # - the part of speech is in the dictionary but not in the wordlist.
    #
    # otherwise this form lets us add tags to new parts of speech that we are adding to the dictionary, or
    # modify tags for parts of speech that are already in the dictionary.

    wordlist_id = request.args.get('wordlist_id')
    serialized_tag_state = request.args.get('serialized_tag_state')
    redirect_to = request.args.get('redirect_to', 'dlernen.lookup_word')
    relation_id = request.args.get('relation_id')

    url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message="1: %s" % r.text,
                               status_code=r.status_code)

    pos_structure = r.json()
    form_data = {}

    wordlist_obj = None
    if wordlist_id:
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist_obj = r.json()

    for p in pos_structure:
        if wordlist_obj and wordlist_obj['list_type'] == 'smart' and not p['word_id']:
            # if this is a smart list, do not even render any part of speech for a word that is
            # not in it.
            continue

        form_data[p['pos_name']] = []
        for a in p['attributes']:
            t = ['attr', p['pos_id'], a['attribute_id']]
            if p['word_id']:
                t.append(p['word_id'])

            t = list(map(str, t))  # convert to str so join won't choke
            field_name = '-'.join(t)
            field_value = a['attrvalue'] if a['attrvalue'] else ""
            d = {
                'field_name': field_name,
                'field_value': field_value,
                'label': a['attrkey'],
                'sort_order': a['sort_order'],
                'enlightened': 'enlightened' if p['word_id'] else '',  # tell CSS to color the text field
                'disabled': False
            }
            form_data[p['pos_name']].append(d)
        form_data[p['pos_name']] = sorted(form_data[p['pos_name']], key=lambda x: x['sort_order'])

    # get tags for any words that have them.  join them as a single space-separated string.
    if wordlist_obj:
        # the wordlist object already has the tags for the words.  traverse the wordlist and create a map of word_ids
        # to tag strings.
        word_id_to_tag_string = {w['word_id']: ' '.join(w['tags']) for w in wordlist_obj['words']}

        for p in pos_structure:
            field_disabled = False
            tags = ''
            if p['word_id']:
                if p['word_id'] not in word_id_to_tag_string:
                    # p['word_id'] is not in the word list.  no big deal.
                    field_disabled = True
                else:
                    tags = word_id_to_tag_string[p['word_id']]
                field_name_parts = ['tag', str(p['pos_id']), str(p['word_id'])]  # convert to str so join won't choke
            else:
                field_name_parts = ['tag', str(p['pos_id'])]  # convert to str so join won't choke

            field_name = '-'.join(field_name_parts)

            # tags aren't attributes, so they don't have a sort order per POS.  fake one by finding the max
            # sort order for this POS and adding 1 to it.
            if wordlist_obj['list_type'] != 'smart':
                d = {
                    'field_name': field_name,
                    'field_value': tags,
                    'label': 'tags',
                    'sort_order': max([x['sort_order'] for x in p['attributes']]) + 1,
                    'enlightened': 'enlightened' if p['word_id'] else '',  # tell CSS to color the text field
                    'disabled': field_disabled
                }

                form_data[p['pos_name']].append(d)

        return render_template('word_editor.html',
                               word=word,
                               form_data=form_data,
                               redirect_to=redirect_to,
                               relation_id=relation_id,
                               tag_state=TagState.deserialize(serialized_tag_state))

    return render_template('word_editor.html',
                           word=word,
                           form_data=form_data,
                           redirect_to=redirect_to,
                           relation_id=relation_id)


@bp.route('/word_editor', methods=['POST'])
def update_dict():
    # hitting the submit button in the word editor brings us here.

    # go through the text fields in the request to distinguish what words are being edited and added.
    # for those words whose attributes we are modifying, delete all the attributes and re-add the values.  easier and
    # cheaper than diffing.
    #
    # to each of the update and add payloads, add the word.  for the update case, this is necessary in case we are
    # making a spelling change.
    #
    # returns a dictionary mapping (word, pos_id) --> word_id
    #
    wordlist_id = request.form.get('wordlist_id')
    relation_id = request.form.get('relation_id')
    redirect_to = request.form.get('redirect_to', 'dlernen.lookup_word')
    word = request.form.get('word', '').strip()

    # maps word_ids to WORD_UPDATE_PAYLOAD_SCHEMA docs
    word_ids_to_update_payloads = {}
    word_ids_to_delete_payloads = {}

    # maps (word, pos_id) pairs to WORD_ADD_PAYLOAD_SCHEMA docs
    word_pos_to_add_payloads = {}

    # mapping of (word, pos_id) to word_id.
    word_pos_to_word_id = {}

    for field_name, value_unstripped in request.form.items():
        parts = field_name.split('-')
        if parts[0] != 'attr':
            continue

        value = value_unstripped.strip()
        pos_id = int(parts[1])
        attribute_id = int(parts[2])
        word_id = int(parts[3]) if len(parts) > 3 else None

        t = (word, pos_id)
        # if there is a word_id, we are updating; otherwise we are adding.
        if word_id:
            if word_id not in word_ids_to_update_payloads:
                word_ids_to_update_payloads[word_id] = {
                    'word': word,
                    'attributes': []
                }
            payload = word_ids_to_update_payloads[word_id]
            if value:
                payload['attributes'].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

            if word_id not in word_ids_to_delete_payloads:
                word_ids_to_delete_payloads[word_id] = {
                    'attributes': []
                }
            payload = word_ids_to_delete_payloads[word_id]
            payload['attributes'].append(
                {
                    'attribute_id': attribute_id
                }
            )

            word_pos_to_word_id[t] = word_id

        else:
            if t not in word_pos_to_add_payloads:
                word_pos_to_add_payloads[t] = {
                    'word': word,
                    'pos_id': t[1],
                    'attributes': []
                }
            payload = word_pos_to_add_payloads[t]
            if value:
                payload['attributes'].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

    # get rid of payloads with empty attribute lists
    word_pos_to_add_payloads = {k: v for k, v in word_pos_to_add_payloads.items() if len(v['attributes']) > 0}
    word_ids_to_update_payloads = {k: v for k, v in word_ids_to_update_payloads.items() if len(v['attributes']) > 0}

    # drop all the attribute values for existing words
    for word_id, payload in word_ids_to_delete_payloads.items():
        r = requests.put(url_for('api_word.update_word', word_id=word_id, _external=True), json=payload)
        if not r:
            flash("could not update word_id %s [%s]:  %s" % (word_id, r.status_code, r.text))

    # add back all the attribute values we pulled from the form.
    for word_id, payload in word_ids_to_update_payloads.items():
        r = requests.put(url_for('api_word.update_word', word_id=word_id, _external=True), json=payload)
        if not r:
            flash("could not update word_id %s [%s]:  %s" % (word_id, r.status_code, r.text))

    for t, payload in word_pos_to_add_payloads.items():
        _, pos_id = t
        url = url_for('api_word.add_word', _external=True)
        r = requests.post(url, json=payload)
        if not r:
            message = "could not add word %s [%s]:  %s" % (word, r.status_code, r.text)
            return render_template("error.html",
                                   message=message,
                                   status_code=r.status_code)

        obj = r.json()
        word_pos_to_word_id[(word, pos_id)] = obj['word_id']

    # if there is a wordlist_id, add all the word ids to the wordlist.  just add all of them; adding a word id that
    # is already there does nothing.

    word_ids = list(word_pos_to_word_id.values())
    if wordlist_id and word_ids:
        payload = {
            'word_ids': word_ids
        }
        r = requests.put(url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id, _external=True),
                         json=payload)
        if not r:
            message = "could not update wordlist %s:  %s [%s]" % (wordlist_id, r.status_code, r.text)
            return render_template("error.html",
                                   message=message,
                                   status_code=r.status_code)

    # now we deal with the tags.

    if wordlist_id:
        # first, drop all the tags for each word_id in the wordlist.

        for word_id in word_pos_to_word_id.values():
            r = requests.delete(url_for('api_wordlist_tag.delete_tags_for_word_id',
                                        word_id=word_id,
                                        wordlist_id=wordlist_id,
                                        _external=True))
            if r.status_code == 400:
                # word id is not in the word list.  no big deal.
                continue

        # next, add back the tags that we pull from the form.

        for field_name, value_unstripped in request.form.items():
            parts = field_name.split('-')
            if parts[0] != 'tag':
                continue

            pos_id = int(parts[1])
            if (word, pos_id) not in word_pos_to_word_id:
                continue

            tag_str = request.form.get(field_name)
            tags = tag_str.split()
            if not tags:
                continue

            payload = [
                {
                    'word_id': word_pos_to_word_id[(word, pos_id)],
                    'tags': tags
                }
            ]

            r = requests.post(url_for('api_wordlist_tag.add_tags',
                                      wordlist_id=wordlist_id,
                                      _external=True),
                              json=payload)
            if not r:
                return render_template("error.html",
                                       message="add tags failed (wordlist_id %s):  %s [%s]" %
                                               (wordlist_id, r.text, r.status_code),
                                       status_code=r.status_code)

        # in case we added a new tag while editing the word
        tag_state_object = TagState.deserialize(request.form.get('serialized_tag_state'))
        tag_state_object.update()

        if relation_id:
            target = url_for(redirect_to,
                             word=word,
                             relation_id=relation_id,
                             serialized_tag_state=tag_state_object.serialize(),
                             wordlist_id=wordlist_id)
        else:
            target = url_for(redirect_to,
                             word=word,
                             serialized_tag_state=tag_state_object.serialize(),
                             wordlist_id=wordlist_id)
    else:
        target = url_for(redirect_to, word=word)

    return redirect(target)


@bp.route('/quiz_report/<string:quiz_key>/<int:wordlist_id>')
def quiz_report(quiz_key, wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    selected_tags = []
    if not serialized_tag_state:
        tag_state = TagState(wordlist_id)
    else:
        tag_state = TagState.deserialize(serialized_tag_state)
        selected_tags = tag_state.selected_tags()

    r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_obj = r.json()

    r = requests.get(url_for('api_quiz.get_report',
                             quiz_key=quiz_key,
                             wordlist_id=wordlist_id,
                             tag=selected_tags,
                             _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    report = r.json()
    return render_template("quiz_report.html",
                           quiz_key=report['quiz_key'],
                           wordlist=wordlist_obj,
                           tag_state=tag_state,
                           scores=report['scores'])


@bp.route('/study_guide/<int:wordlist_id>')
def study_guide(wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    selected_tags = []
    if not serialized_tag_state:
        tag_state = TagState(wordlist_id)
    else:
        tag_state = TagState.deserialize(serialized_tag_state)
        selected_tags = tag_state.selected_tags()

    r = requests.get(url_for('api_wordlist.get_wordlist',
                             tag=selected_tags,
                             wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist_obj = r.json()

    # go through the wordlist and organize everything by tag.  invert the mapping of words to
    # tags that appears in the wordlist.

    tags_to_words = {}
    untagged_words = list(filter(lambda x: not x['tags'], wordlist_obj['words']))
    for word in wordlist_obj['words']:
        for t in word['tags']:
            if t not in tags_to_words:
                tags_to_words[t] = []
            tags_to_words[t].append(word)

    # sort everything
    untagged_words = sorted(untagged_words, key=lambda x: x['word'].casefold())
    tags = sorted(tags_to_words.keys())
    tags_to_words = {t: sorted(tags_to_words[t], key=lambda x: x['word'].casefold()) for t in tags}

    return render_template("study_guide.html",
                           tags=tags,
                           tag_state=tag_state,
                           untagged_words=untagged_words,
                           tags_to_words=tags_to_words,
                           wordlist=wordlist_obj)


def __submit_to_wordlist(serialized_tag_state, word, redirect_to):
    tag_state = TagState.deserialize(serialized_tag_state)
    wordlist_id = tag_state.wordlist_id

    if not word:
        return redirect(url_for(redirect_to,
                                wordlist_id=wordlist_id,
                                serialized_tag_state=serialized_tag_state,
                                _external=True))

    r = requests.get(url_for('api_word.get_word', word=word, _external=True))
    if r:
        obj = r.json()
        word_ids = [x['word_id'] for x in obj]
        payload = {
            "word_ids": word_ids
        }

        r2 = requests.put(url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id, _external=True),
                          json=payload)
        if not r2:
            flash(r2.text)

    elif r.status_code == 404:
        return redirect(url_for('dlernen.edit_word_form',
                                word=word,
                                wordlist_id=wordlist_id,
                                serialized_tag_state=serialized_tag_state,
                                redirect_to=redirect_to,
                                _external=True))

    else:
        flash(r.text)

    return redirect(url_for('dlernen.edit_word_form',
                            word=word,
                            wordlist_id=wordlist_id,
                            serialized_tag_state=serialized_tag_state,
                            redirect_to=redirect_to,
                            _external=True))


@bp.route('/update_words', methods=['POST'])
def add_word_submit():
    # submitting from the add word field in the sidebar will bring us here.

    # this will update the prevailing word list with the word in the request.  if that word isn't in the dictionary,
    # redirect to the word edit page.  on submit, go to <redirect_to>.

    word = request.form.get('add_word').strip()
    serialized_tag_state = request.form.get('serialized_tag_state')
    redirect_to = request.form.get('redirect_to')
    # print("add_word_submit:  redirect_to = %s" % redirect_to)
    if serialized_tag_state:
        return __submit_to_wordlist(serialized_tag_state, word, redirect_to)

    if not word:
        return redirect(url_for(redirect_to, _external=True))

    r = requests.get(url_for('api_word.get_word', word=word, partial='true', _external=True))

    if r.status_code == 404:
        return redirect(url_for('dlernen.edit_word_form',
                                word=word,
                                redirect_to='dlernen.lookup_word',
                                _external=True))

    if not r:
        flash(r.text)

    return redirect(url_for('dlernen.lookup_word',
                            word=word,
                            _external=True))


@bp.route('/update_via_search_results', methods=['POST'])
def update_via_search_results():
    # the submit button under the matching words in the search results page brings us here.  of the matching
    # words, remove all from the word list and add back the ones that were selected.

    serialized_tag_state = request.form.get('serialized_tag_state')
    search_term = request.form.get('search_term')
    matching_word_ids = json.loads(request.form.get('matching_word_ids'))
    selected_word_ids = request.form.getlist('selected', type=int)

    tag_state = TagState.deserialize(serialized_tag_state)
    wordlist_id = tag_state.wordlist_id

    # remove matching_word_ids from list.  not all will be in it to begin with but this should be ok.
    r = requests.put(url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id,
                             _external=True),
                     json={
                         'word_ids': matching_word_ids
                     })
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    # add back the ones marked 'selected'
    r = requests.put(url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id,
                             _external=True),
                     json={
                         'word_ids': selected_word_ids
                     })
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    # add the tags that were in the selected words' fields
    payload = []
    for x in selected_word_ids:
        tags = request.form.get('tag-%s' % x).strip().split()
        payload.append({
            'word_id': x,
            'tags': tags
        })

    if payload:
        r = requests.post(url_for('api_wordlist_tag.add_tags',
                                  wordlist_id=wordlist_id,
                                  _external=True),
                          json=payload)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

    return redirect(url_for('dlernen.lookup_word',
                            word=search_term,
                            partial='true',
                            serialized_tag_state=serialized_tag_state))
