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

        # decorate the search result keys with a boolean indicating list membership
        for r in search_results:
            r['word']['is_member'] = r['word']['word_id'] in matching_member_word_ids

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
        for k in tag_textfield_keys:
            new_tags = request.form.get(k, '').strip().split()
            if not new_tags:
                continue
            _, word_id = k.split('-')
            word_id = int(word_id)
            url = url_for('api_wordlist_tag.add_tags',
                          wordlist_id=wordlist_id,
                          word_id=word_id,
                          _external=True)
            r = requests.post(url, json=new_tags)
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
    print("edit_word_form:  redirect_to = %s" % redirect_to)

    url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message="1: %s" % r.text,
                               status_code=r.status_code)

    pos_structure = r.json()
    form_data = {p['pos_name']: [] for p in pos_structure}

    # field_values_before is a mapping of field names to field values, and contains the values of the
    # attributes as retrieved from the database - before they are changed.  when the form is submitted,
    # we will get another such mapping, with whatever changes were made.  we implement the dictionary
    # update by diffing these and making the appropriate changes to the database.

    field_values_before = {}

    for p in pos_structure:
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
                'disabled': False
            }
            form_data[p['pos_name']].append(d)
            field_values_before[field_name] = field_value
        form_data[p['pos_name']] = sorted(form_data[p['pos_name']], key=lambda x: x['sort_order'])

    # get tags for any words that have them.  join them as a single space-separated string.
    if wordlist_id:
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist_obj = r.json()

        for p in pos_structure:
            field_disabled = False
            if p['word_id']:
                url = url_for('api_wordlist_tag.get_tags',
                              wordlist_id=wordlist_id,
                              word_id=p['word_id'],
                              _external=True)
                r = requests.get(url)
                if r.status_code == 404:
                    # p['word_id'] is not in the word list.  no big deal.
                    field_disabled = True
                    tags = ''
                elif not r:
                    return render_template("error.html",
                                           message="2: %s" % r.text,
                                           status_code=r.status_code)
                else:
                    tags_result = r.json()
                    tags = ' '.join(tags_result['tags'])
                field_name_parts = ['tag', str(p['pos_id']), str(p['word_id'])]  # convert to str so join won't choke
            else:
                tags = ''
                field_name_parts = ['tag', str(p['pos_id'])]  # convert to str so join won't choke

            field_name = '-'.join(field_name_parts)
            field_values_before[field_name] = tags

            # tags aren't attributes, so they don't have a sort order per POS.  fake one by finding the max
            # sort order for this POS and adding 1 to it.
            if wordlist_obj['list_type'] != 'smart':
                d = {
                    'field_name': field_name,
                    'field_value': tags,
                    'label': 'tags',
                    'sort_order': max([x['sort_order'] for x in p['attributes']]) + 1,
                    'disabled': field_disabled
                }

                form_data[p['pos_name']].append(d)

        return render_template('word_editor.html',
                               word=word,
                               form_data=form_data,
                               redirect_to=redirect_to,
                               relation_id=relation_id,
                               field_values_before=json.dumps(field_values_before),
                               tag_state=TagState.deserialize(serialized_tag_state))

    return render_template('word_editor.html',
                           word=word,
                           form_data=form_data,
                           redirect_to=redirect_to,
                           relation_id=relation_id,
                           field_values_before=json.dumps(field_values_before))


def diff_attr_values(pos_id, attribute_id, word_id,
                     value_before, value_after, word, word_payloads, word_pos_to_word_id):
    # helper function for update_dict(), created by the magic extract-method feature.

    t = (word, pos_id)
    if t not in word_payloads:
        word_payloads[t] = {}
    payload = word_payloads[t]
    if word_id:
        word_pos_to_word_id[t] = word_id

    value_before_stripped = value_before.strip()
    value_after_stripped = value_after.strip()

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
        payload[js.ATTRIBUTES].append({'attrvalue': value_after,
                                       'attribute_id': attribute_id})

    elif value_after_stripped != value_before_stripped:
        # we are changing an existing value.
        # we will have a word_id
        if js.ATTRIBUTES not in payload:
            payload[js.ATTRIBUTES] = []
        payload[js.ATTRIBUTES].append({'attribute_id': attribute_id,
                                       'attrvalue': value_after})

    else:
        # stripped values are unchanged, but it may happen that the unstripped values are different
        # because we added/removed leading/trailing whitespace and did nothing else.
        if value_after_stripped and (value_before != value_after):
            if js.ATTRIBUTES not in payload:
                payload[js.ATTRIBUTES] = []
            payload[js.ATTRIBUTES].append({'attribute_id': attribute_id,
                                           'attrvalue': value_after})


@bp.route('/word_editor', methods=['POST'])
def update_dict():
    # hitting the submit button in the word editor brings us here.

    word = request.form.get('word', '').strip()
    word_before = request.form.get('word_before')
    wordlist_id = request.form.get('wordlist_id')
    relation_id = request.form.get('relation_id')
    redirect_to = request.form.get('redirect_to', 'dlernen.lookup_word')
    print("update_dict:  redirect_to = %s" % redirect_to)
    field_values_before = json.loads(request.form.get('field_values_before'))
    field_values_after = {k: request.form.get(k, '') for k in field_values_before.keys()}

    # go through all the attribute values and diff before/after.  we will construct add/update
    # payloads and send them off to the API.  we will have to construct one request per
    # word added/modified until i get around to batching it all in a single request.

    # we have to construct payloads for each (word, pos_id) that has changes.
    # make a dict mapping these tuples to payload objects.  also track whether
    # (word, pos_id) is associated with a word id.  if not, then we are adding.

    # maps (word, pos_id) 2ples to WORD_UPDATE_PAYLOAD_SCHEMA docs.
    word_payloads = {}

    # maps (word, pos_id) 2ples to word_id (if there is one for this word/pos_id)
    word_pos_to_word_id = {}

    for field_name in field_values_before.keys():
        parts = field_name.split('-')
        if parts[0] == 'attr':
            pos_id = int(parts[1])
            attribute_id = int(parts[2])
            word_id = int(parts[3]) if len(parts) > 3 else None
            diff_attr_values(pos_id, attribute_id, word_id,
                             field_values_before[field_name],
                             field_values_after[field_name], word, word_payloads, word_pos_to_word_id)

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
    # update/add the word and the attribute values

    for k, payload in word_payloads.items():
        if k in word_pos_to_word_id:
            # we are updating
            word_id = word_pos_to_word_id[k]
            url = url_for('api_word.update_word', word_id=word_id, _external=True)
            r = requests.put(url, json=payload)
            if not r:
                flash("could not update word %s [%s]:  %s" % (word, r.status_code, r.text))
        else:
            # we are adding a new word.
            url = url_for('api_word.add_word', _external=True)
            r = requests.post(url, json=payload)
            if not r:
                message = "could not insert word %s [%s]:  %s" % (word, r.status_code, r.text)
                return render_template("error.html",
                                       message=message,
                                       status_code=r.status_code)

            obj = r.json()
            # if we have a wordlist_id, add the newly-minted word to the wordlist.
            if wordlist_id:
                payload = {
                    'word_ids': [obj['word_id']]
                }
                url = url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id, _external=True)
                r = requests.put(url, json=payload)
                if not r:
                    message = "could not add word to wordlist:  word %s, word_id = %s [%s]" % (
                        word, obj['word_id'], r.text)
                    return render_template("error.html",
                                           message=message,
                                           status_code=r.status_code)

            # if we have a relation_id, add the newly-minted word to the relation.
            if relation_id:
                payload = {
                    'word_ids': [obj['word_id']]
                }
                url = url_for('api_relation.update_relation', relation_id=relation_id, _external=True)
                r = requests.put(url, json=payload)
                if not r:
                    message = "could not add word to relation:  word %s, word_id = %s, relation_id = %s: %s" % (
                        word, obj['word_id'], relation_id, r.text)
                    return render_template("error.html",
                                           message=message,
                                           status_code=r.status_code)

    # now we deal with the tags.  at this point every POS in the edit form has a word_id.  get the POS info for
    # this word to get those word ids.  not all of them will be in the wordlist.

    if wordlist_id:
        url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message="get_pos_for_word failed: %s" % r.text,
                                   status_code=r.status_code)

        pos_structure = r.json()

        # this will contain the set of tags based on the tag string (what was entered in the field) for the POS.
        # we will put a pos_id -> tags mapping here if:
        #
        # - a wordlist_id is present
        # - the tag string has been changed.
        #
        # so, word_id_to_tags_adding and word_id_to_tags_deleting will only contain a mapping when the tags for a word
        # have changed.
        pos_id_to_tags_adding = {}
        pos_id_to_tags_deleting = {}

        for field_name in field_values_before.keys():
            parts = field_name.split('-')
            if parts[0] == 'tag':
                tag_str_before = field_values_before[field_name]
                tags_before = set(tag_str_before.split())
                tag_str_after = field_values_after[field_name]
                tags_after = set(tag_str_after.split())

                pos_id = int(parts[1])

                if tags_after != tags_before:
                    pos_id_to_tags_deleting[pos_id] = list(tags_before)
                    pos_id_to_tags_adding[pos_id] = list(tags_after)

        for p in pos_structure:
            if not p['word_id']:
                continue

            if p['pos_id'] not in pos_id_to_tags_deleting:
                continue

            url = url_for('api_wordlist_tag.delete_tags_for_word_id',
                          word_id=p['word_id'],
                          wordlist_id=wordlist_id,
                          tag=pos_id_to_tags_deleting[p['pos_id']],
                          _external=True)
            r = requests.delete(url)
            if r.status_code == 400:
                # word id is not in the word list.  no big deal.
                continue

            if not r:
                return render_template("error.html",
                                       message="delete tags failed (wordlist_id %s, word_id %s):  %s" %
                                               (wordlist_id, p['word_id'], r.text),
                                       status_code=r.status_code)

            url = url_for('api_wordlist_tag.add_tags',
                          word_id=p['word_id'],
                          wordlist_id=wordlist_id,
                          _external=True)
            r = requests.post(url, json=pos_id_to_tags_adding[p['pos_id']])
            if not r:
                return render_template("error.html",
                                       message="add tags failed (wordlist_id %s, word_id %s):  %s [%s]" %
                                               (wordlist_id, p['word_id'], r.text, r.status_code),
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
    pprint(matching_word_ids)
    selected_word_ids = request.form.getlist('selected', type=int)

    tag_state = TagState.deserialize(serialized_tag_state)
    wordlist_id = tag_state.wordlist_id

    # remove matching_word_ids from list.  not all will be in it to begin with but this should be ok.
    r = requests.put(url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id,
                             _external=True),
                     json={
                         'word_ids': matching_word_ids
                     })

    # add back the ones marked 'selected'
    r = requests.put(url_for('api_wordlist.update_wordlist', wordlist_id=wordlist_id,
                             _external=True),
                     json={
                         'word_ids': selected_word_ids
                     })

    return redirect(url_for('dlernen.lookup_word',
                            word=search_term,
                            partial='true',
                            serialized_tag_state=serialized_tag_state))
