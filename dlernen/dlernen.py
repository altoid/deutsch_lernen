from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
import requests
import json
from dlernen import dlernen_json_schema as js
from tagstate import TagState

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


@bp.route('/lookup/<int:word_id>', methods=['GET'])
def lookup_by_id(word_id):
    # for when a word appears as a hyperlink in a page.
    wordlist_id = request.args.get('wordlist_id')
    wordlist = None
    if wordlist_id:
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist = r.json()

    r = requests.get(url_for('api_word.get_word_by_id', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    result = r.json()

    r = requests.get(url_for('api_wordlists.get_wordlists_by_word_id', word_id=word_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    member_wordlists = r.json()

    template_args = [(result, member_wordlists)]

    if wordlist:
        return render_template('lookup.html',
                               word=result["word"],
                               wordlist=wordlist,
                               serialized_tag_state=request.args.get('serialized_tag_state'),
                               template_args=template_args)

    return render_template('lookup.html',
                           word=result["word"],
                           serialized_tag_state=request.args.get('serialized_tag_state'),
                           template_args=template_args)


@bp.route('/lookup', methods=['POST'])
def lookup_by_post():
    # for looking up a word entered into a form.
    word = request.form.get('lookup')
    serialized_tag_state = request.form.get('serialized_tag_state')

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

    results = sorted(results, key=lambda x: str.lower(x['word']))
    template_args = []
    for result in results:
        r = requests.get(url_for('api_wordlists.get_wordlists_by_word_id', word_id=result['word_id'], _external=True))
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)

        member_wordlists = r.json()
        template_args.append((result, member_wordlists))

    # get wordlist if appropriate
    if serialized_tag_state:
        tag_state_object = TagState.deserialize(serialized_tag_state)

        url = url_for('api_wordlist.get_wordlist', wordlist_id=tag_state_object.wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist = r.json()

        return render_template('lookup.html',
                               word=word,
                               wordlist=wordlist,
                               serialized_tag_state=serialized_tag_state,
                               template_args=template_args)

    return render_template('lookup.html',
                           word=word,
                           template_args=template_args)


@bp.route('/wordlists')
def wordlists():
    url = url_for('api_wordlists.get_wordlists', _external=True)
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
    wordlist_metadata = {k: '' if v is None else v for k, v in r.json().items()}

    return render_template('list_attributes.html',
                           serialized_tag_state=request.args.get('serialized_tag_state'),
                           wordlist=wordlist_metadata)


@bp.route('/list_editor/<int:wordlist_id>')
def list_editor(wordlist_id):
    url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)
    wordlist = r.json()

    return render_template('list_editor.html',
                           serialized_tag_state=request.args.get('serialized_tag_state'),
                           wordlist=wordlist)


@bp.route('/wordlist/update_tags/<int:wordlist_id>', methods=['POST'])
def update_tag_state(wordlist_id):
    # the checkboxes are all called "tag"
    tags = request.form.getlist('tag')

    tag_state_object = TagState.deserialize(request.form.get('serialized_tag_state'))

    tag_state_object.clear()
    tag_state_object.set_tags(tags)

    return redirect(url_for('dlernen.wordlist_page',
                            wordlist_id=wordlist_id,
                            serialized_tag_state=tag_state_object.serialize()))


@bp.route('/wordlist/<int:wordlist_id>')
def wordlist_page(wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    if serialized_tag_state:
        tag_state_object = TagState.deserialize(serialized_tag_state)
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
        r2 = requests.get(url_for('api_wordlist.get_wordlist_metadata', wordlist_id=wordlist_id, _external=True))
        metadata = {k: '' if v is None else v for k, v in r2.json().items()}

        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               serialized_tag_state=serialized_tag_state,
                               wordlist_id=metadata['wordlist_id'],
                               wordlist=metadata)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist = r.json()
    if wordlist['notes'] is None:
        # otherwise the word 'None' is rendered in the form
        wordlist['notes'] = ''

    nchunks = request.args.get('nchunks', current_app.config['NCHUNKS'], type=int)
    known_words = chunkify(wordlist['known_words'], nchunks)
    unknown_words = chunkify(wordlist['unknown_words'], nchunks)

    if wordlist['list_type'] == 'smart':
        return render_template('wordlist.html',
                               wordlist=wordlist,
                               tag_state=tag_state_object.tag_state(),
                               known_words=known_words,
                               unknown_words=unknown_words)

    serialized_tag_state = tag_state_object.serialize()

    return render_template('wordlist.html',
                           wordlist=wordlist,
                           tag_state=tag_state_object.tag_state(),
                           serialized_tag_state=serialized_tag_state,
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
                               serialized_tag_state=request.form.get('serialized_tag_state'),
                               wordlist=metadata)

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

    url = url_for('api_wordlist.update_wordlist_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)

    if r.status_code == 422:
        # unprocessable content - the sqlcode is not valid.  redirect to the list attributes page to fix it.
        flash("invalid sqlcode")
        return render_template('list_attributes.html',
                               serialized_tag_state=request.form.get('serialized_tag_state'),
                               wordlist_metadata=metadata)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    return redirect(url_for('dlernen.wordlist_page',
                            serialized_tag_state=request.form.get('serialized_tag_state', ''),
                            wordlist_id=wordlist_id))


@bp.route('/list_editor', methods=['POST'])
def edit_list_contents():
    wordlist_id = request.form.get('wordlist_id')
    button = request.form.get('submit')
    tag_state_object = TagState.deserialize(request.form.get('serialized_tag_state'))

    if button.startswith("Delete"):
        # the checkboxes are called 'removing'

        url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id, _external=True)
        word_ids = list(map(int, request.form.getlist('removing')))
        r = requests.post(url, json={
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
            url = url_for('api_wordlist_tag.delete_tags',
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

    # fetch the wordlist so that its current state can be rendered
    get_wordlist_url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.get(get_wordlist_url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)
    wordlist = r.json()

    return render_template('list_editor.html',
                           serialized_tag_state=tag_state_object.serialize(),
                           wordlist=wordlist)


@bp.route('/add_to_list', methods=['POST'])
def add_to_list():
    # the get_word function will check that the word is not garbage, no need to do it here.
    word = request.form['word'].strip()
    wordlist_id = request.form['wordlist_id']

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
        target = url_for('dlernen.wordlist_page',
                         serialized_tag_state=request.form.get('serialized_tag_state', ''),
                         wordlist_id=wordlist_id)
        return redirect(target)

    url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)
    if not r:
        flash(r.text)

    target = url_for('dlernen.wordlist_page',
                     wordlist_id=wordlist_id,
                     serialized_tag_state=request.form.get('serialized_tag_state', ''))
    return redirect(target)


@bp.route('/update_notes', methods=['POST'])
def update_notes():
    wordlist_id = request.form['wordlist_id']

    payload = {
        'notes': request.form['notes']
    }

    url = url_for('api_wordlist.update_wordlist_contents', wordlist_id=wordlist_id, _external=True)
    r = requests.put(url, json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    target = url_for('dlernen.wordlist_page',
                     wordlist_id=wordlist_id,
                     serialized_tag_state=request.form.get('serialized_tag_state', ''))

    return redirect(target)


@bp.route('/delete_from_list', methods=['POST'])
def delete_from_list():
    wordlist_id = request.form['wordlist_id']

    url = url_for('api_wordlist.delete_from_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.post(url, json={
        "unknown_words": request.form.getlist('unknown_wordlist')
    })
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    target = url_for('dlernen.wordlist_page',
                     serialized_tag_state=request.form.get('serialized_tag_state', ''),
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

    # FIXME - tags field should be disabled for smart lists

    wordlist_id = request.args.get('wordlist_id')
    serialized_tag_state = request.args.get('serialized_tag_state')

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
        for p in pos_structure:
            field_disabled = False
            if p['word_id']:
                url = url_for('api_wordlist_tag.get_tags',
                              wordlist_id=wordlist_id,
                              word_id=p['word_id'],
                              _external=True)
                r = requests.get(url)
                if r.status_code == 400:
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
                field_name_parts = ['tag', str(p['pos_id']), str(p['word_id'])]  # convert to str to join won't choke
            else:
                tags = ''
                field_name_parts = ['tag', str(p['pos_id'])]  # convert to str to join won't choke

            field_name = '-'.join(field_name_parts)
            field_values_before[field_name] = tags

            # tags aren't attributes, so they don't have a sort order per POS.  fake one by finding the max
            # sort order for this POS and adding 1 to it.
            d = {
                'field_name': field_name,
                'field_value': tags,
                'label': 'tags',
                'sort_order': max([x['sort_order'] for x in p['attributes']]) + 1,
                'disabled': field_disabled
            }
            form_data[p['pos_name']].append(d)

        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist = r.json()

        return render_template('word_editor.html',
                               word=word,
                               wordlist=wordlist,
                               form_data=form_data,
                               serialized_tag_state=serialized_tag_state,
                               field_values_before=json.dumps(field_values_before))

    return render_template('word_editor.html',
                           word=word,
                           form_data=form_data,
                           serialized_tag_state=serialized_tag_state,
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
    word = request.form.get('word', '').strip()
    word_before = request.form.get('word_before')
    wordlist_id = request.form.get('wordlist_id')
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
                flash("could not insert word %s [%s]:  %s" % (word, r.status_code, r.text))

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

            url = url_for('api_wordlist_tag.delete_tags',
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
                                       message="add tags failed (wordlist_id %s, word_id %s):  %s" %
                                               (wordlist_id, p['word_id'], r.text),
                                       status_code=r.status_code)

    if wordlist_id:
        target = url_for('dlernen.wordlist_page',
                         serialized_tag_state=request.form.get('serialized_tag_state', ''),
                         wordlist_id=wordlist_id)
    else:
        # if we didn't add a word to any list, return to the editing form for this word.
        target = url_for('dlernen.edit_word_form', word=word)

    return redirect(target)


@bp.route('/quiz_report/<string:quiz_key>/<int:wordlist_id>')
def quiz_report(quiz_key, wordlist_id):
    r = requests.get(url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist = r.json()

    url = url_for('api_quiz.get_report', quiz_key=quiz_key, wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    report = r.json()
    return render_template("quiz_report.html",
                           quiz_key=report['quiz_key'],
                           wordlist=wordlist,
                           serialized_tag_state=request.args.get('serialized_tag_state'),
                           scores=report['scores'])


@bp.route('/study_guide/<int:wordlist_id>')
def study_guide(wordlist_id):
    serialized_tag_state = request.args.get('serialized_tag_state')
    tag_state_object = TagState.deserialize(serialized_tag_state)
    selected_tags = tag_state_object.selected_tags()

    r = requests.get(url_for('api_wordlist.get_wordlist',
                             tag=selected_tags,
                             wordlist_id=wordlist_id, _external=True))
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist = r.json()

    # go through the wordlist and organize everything by tag.  invert the mapping of words to
    # tags that appears in the wordlist.

    tags_to_words = {}
    untagged_words = []
    for word in wordlist['known_words']:
        if not word['tags']:
            untagged_words.append(word)
            continue

        for t in word['tags']:
            if t not in tags_to_words:
                tags_to_words[t] = []
            tags_to_words[t].append(word)

    # sort everything
    untagged_words = sorted(untagged_words, key=lambda x: x['word'].casefold())
    tags = sorted(tags_to_words.keys())
    for t in tags:
        tags_to_words[t] = sorted(tags_to_words[t], key=lambda x: x['word'].casefold())

    return render_template("study_guide.html",
                           tags=tags,
                           serialized_tag_state=serialized_tag_state,
                           untagged_words=untagged_words,
                           tags_to_words=tags_to_words,
                           wordlist=wordlist)
