from flask import Blueprint, request, render_template, redirect, url_for, flash, current_app
import requests
import json
from dlernen.tagstate import TagState
from dlernen_json_schema import ATTRIBUTES
from dlernen.api_pos import \
    VERB_POS_NAME, \
    SEPARABLE_PREFIX_POS_NAME, \
    INSEPARABLE_PREFIX_POS_NAME
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
    tag_state = TagState.deserialize(serialized_tag_state) if serialized_tag_state else None
    if tag_state:
        # see which of the search results are already in the wordlist.
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


def get_related_verbs(verbobject):
    url = None
    if verbobject['pos_name'] == VERB_POS_NAME:
        url = url_for('api_verbs.get_verbs_by_grundverb', grundverb=verbobject['word'], _external=True)
    elif verbobject['pos_name'] == SEPARABLE_PREFIX_POS_NAME:
        url = url_for('api_verbs.get_verbs_by_prefix', prefix=verbobject['word'], _external=True)
    elif verbobject['pos_name'] == INSEPARABLE_PREFIX_POS_NAME:
        url = url_for('api_verbs.get_verbs_by_prefix', prefix=verbobject['word'], _external=True)

    if not url:
        return []

    r = requests.get(url)
    if r.status_code == 404:
        return []

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    verbinfo_arr = r.json()

    # pull out all of the word ids in all the verbinfos, then get the corresponding displayable words.  this lets us
    # get all of them in a single request.  figure out what goes where later.

    word_ids = []
    for x in verbinfo_arr:
        word_ids.append(x['grundverb_word_id'])
        word_ids.append(x['word_id'])
        if x['prefix_word_id']:
            word_ids.append(x['prefix_word_id'])

    r = requests.put(url_for('api_words.get_words_from_word_ids', _external=True),
                     json={
                         'word_ids': word_ids
                     })
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordobjects = r.json()
    word_ids_to_words = {x['word_id']: x for x in wordobjects}

    # decorate the verb respons info with the word objects
    for x in verbinfo_arr:
        x['grundverb_word_obj'] = word_ids_to_words[x['grundverb_word_id']]
        x['word_obj'] = word_ids_to_words[x['word_id']]
        if x['prefix_word_id']:
            x['prefix_word_obj'] = word_ids_to_words[x['prefix_word_id']]

    verbinfo_arr = sorted(verbinfo_arr, key=lambda x: x['word_obj']['word'])

    return verbinfo_arr


@bp.route('/word/<int:word_id>', methods=['GET'])
def lookup_by_id(word_id):
    # for when a word appears as a hyperlink in a page.

    serialized_tag_state = request.args.get('serialized_tag_state')

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

    related_verbs = get_related_verbs(wordobject)
    tag_state = TagState.deserialize(serialized_tag_state) if serialized_tag_state else None

    return render_template('word.html',
                           wordobject=wordobject,
                           member_wordlists=member_wordlists,
                           relations=relations,
                           related_verbs=related_verbs,
                           tag_state=tag_state)


@bp.route('/lookup', methods=['POST'])
def lookup_submit():
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
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    result = r.json()
    return render_template('wordlists.html', rows=result)


@bp.route('/wordlist/attributes/<int:wordlist_id>')
def wordlist_attributes(wordlist_id):
    url = url_for('api_wordlist.get_metadata', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)
    wordlist_metadata = {k: '' if v is None else v for k, v in r.json().items()}

    return render_template('wordlist_attributes.html',
                           wordlist_metadata=wordlist_metadata,
                           tag_state=TagState.deserialize(request.args.get('serialized_tag_state')))


@bp.route('/wordlist/editor/<int:wordlist_id>')
def wordlist_editor(wordlist_id):
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

    return render_template('wordlist_editor.html',
                           tag_state=tag_state,
                           wordlist=wordlist_obj)


@bp.route('/wordlist/tags/<int:wordlist_id>', methods=['POST'])
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
        return render_template('wordlist_attributes.html',
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


@bp.route('/wordlists', methods=['POST'])
def wordlists_submit():
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


@bp.route('/wordlist/attributes', methods=['POST'])
def wordlist_attributes_submit():
    # note that the values in the form have not been subject to json schema validation.  these are just
    # whatever bullshit was entered into the form (the wordlist_attributes template).  so we have to
    # fiddle with the values before stuffing them into the payload, which IS validated.

    serialized_tag_state = request.form.get('serialized_tag_state')
    tag_state = TagState.deserialize(serialized_tag_state)
    name = request.form.get('name', '')
    citation = request.form.get('citation', '')
    sqlcode = request.form.get('sqlcode', '')

    wordlist_id = tag_state.wordlist_id
    list_type = tag_state.list_type

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
        return render_template('wordlist_attributes.html',
                               tag_state=tag_state,
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
        return render_template('wordlist_attributes.html',
                               tag_state=tag_state,
                               wordlist_metadata=metadata)

    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    return redirect(url_for('dlernen.wordlist',
                            serialized_tag_state=serialized_tag_state,
                            wordlist_id=wordlist_id))


@bp.route('/wordlist/editor', methods=['POST'])
def wordlist_editor_submit():
    button = request.form.get('submit')
    serialized_tag_state = request.form.get('serialized_tag_state')
    tag_state_object = TagState.deserialize(serialized_tag_state)
    wordlist_id = tag_state_object.wordlist_id

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

    return redirect(url_for('dlernen.wordlist_editor',
                            serialized_tag_state=serialized_tag_state,
                            wordlist_id=wordlist_id,
                            _external=True))


@bp.route('/wordlist/notes', methods=['POST'])
def wordlist_notes_submit():
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


@bp.route('/word/notes', methods=['POST'])
def word_notes_submit():
    word_id = request.form.get('word_id')
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
                     serialized_tag_state=serialized_tag_state)

    return redirect(target)


@bp.route('/word/editor/<string:word>', methods=['GET'])
def word_editor(word):
    # construct the editing form for this word, with all attributes for all parts of speech.
    # field name formats are described in word_editor.html.  a tags field
    # will NOT appear for the part of speech if:
    #
    # - no wordlist_id is present OR
    # - the part of speech is in the dictionary but not in the wordlist.
    #
    # otherwise this form lets us add tags to new parts of speech that we are adding to the dictionary, or
    # modify tags for parts of speech that are already in the dictionary.

    redirect_to = request.args.get('redirect_to', 'dlernen.lookup_word')
    relation_id = request.args.get('relation_id')

    wordlist_id = None
    tag_state_object = None
    serialized_tag_state = request.args.get('serialized_tag_state')
    if serialized_tag_state:
        tag_state_object = TagState.deserialize(serialized_tag_state)
        wordlist_id = tag_state_object.wordlist_id

    url = url_for('api_pos.get_pos_for_word', word=word, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message="1: %s" % r.text,
                               status_code=r.status_code)

    pos_structure = r.json()
    form_data = {}

    wordlist_obj = None
    member_word_ids = set()
    if wordlist_id:
        url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
        r = requests.get(url)
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        wordlist_obj = r.json()
        member_word_ids = {x['word_id'] for x in wordlist_obj['words']}

    for p in pos_structure:
        if wordlist_obj and wordlist_obj['list_type'] == 'smart':
            # if this is a smart list, do not even render any part of speech for a word that is
            # not in it.
            if not p['word_id']:
                continue

            if p['word_id'] not in member_word_ids:
                continue

        form_data[p['pos_name']] = []
        for a in p[ATTRIBUTES]:
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
                    'sort_order': max([x['sort_order'] for x in p[ATTRIBUTES]]) + 1,
                    'enlightened': 'enlightened' if p['word_id'] else '',  # tell CSS to color the text field
                    'disabled': field_disabled
                }

                form_data[p['pos_name']].append(d)

    return render_template('word_editor.html',
                           word=word,
                           form_data=form_data,
                           redirect_to=redirect_to,
                           relation_id=relation_id,
                           tag_state=tag_state_object)


@bp.route('/word/editor', methods=['POST'])
def word_editor_submit():
    # hitting the submit button in the word editor brings us here.

    # go through the text fields in the request to distinguish what words are being edited and added.
    # for those words whose attributes we are modifying, delete all the attributes and re-add the values.  easier and
    # cheaper than diffing.
    #
    # to each of the update and add payloads, add the word.  for the update case, this is necessary in case we are
    # making a spelling change.
    #
    wordlist_id = None
    tag_state_object = None
    serialized_tag_state = request.form.get('serialized_tag_state')
    if serialized_tag_state:
        # in case we added a new tag while editing the word
        tag_state_object = TagState.deserialize(serialized_tag_state)
        tag_state_object.update()
        wordlist_id = tag_state_object.wordlist_id

    relation_id = request.form.get('relation_id')
    redirect_to = request.form.get('redirect_to', 'dlernen.lookup_word')

    # there are two incarnations of the word being edited:  the word itself, as pulled from the word table,
    # and the word as pulled from the 'word' text field.  these will be the same, unless we have altered the word in
    # the text field, e.g. changing the spelling.  the form must be well-behaved if the word field is cleared.

    word_original = request.form.get('word_original')
    word = request.form.get('word', '').strip()

    if not word:
        target = url_for('dlernen.word_editor',
                         word=word_original,
                         serialized_tag_state=serialized_tag_state,  # can be None
                         redirect_to=redirect_to,
                         relation_id=relation_id,
                         _external=True)

        flash("word field has been cleared; that's not right")
        return redirect(target)

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
                    ATTRIBUTES: []
                }
            payload = word_ids_to_update_payloads[word_id]
            if value:
                payload[ATTRIBUTES].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

            if word_id not in word_ids_to_delete_payloads:
                word_ids_to_delete_payloads[word_id] = {
                    ATTRIBUTES: []
                }
            payload = word_ids_to_delete_payloads[word_id]
            payload[ATTRIBUTES].append(
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
                    ATTRIBUTES: []
                }
            payload = word_pos_to_add_payloads[t]
            if value:
                payload[ATTRIBUTES].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

    # get rid of payloads with empty attribute lists
    word_pos_to_add_payloads = {k: v for k, v in word_pos_to_add_payloads.items() if len(v[ATTRIBUTES]) > 0}
    word_ids_to_update_payloads = {k: v for k, v in word_ids_to_update_payloads.items() if len(v[ATTRIBUTES]) > 0}

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

    word_ids = list(word_pos_to_word_id.values())

    # if there aren't any word ids, then the form was submitted with no fields filled in and there is no part of
    # speech with this word.  redirect back to the form.

    if not word_ids:
        flash("""no words created""")
        return redirect(url_for('dlernen.word_editor',
                                word=word,
                                serialized_tag_state=request.form.get('serialized_tag_state'),
                                redirect_to=redirect_to,
                                _external=True))

    # if there is a wordlist_id, add all the word ids to the wordlist.  just add all of them; adding a word id that
    # is already there does nothing.

    if wordlist_id:
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

    # if there is a relation id, add all the word ids to the relation.

    if relation_id:
        payload = {
            'word_ids': word_ids
        }
        r = requests.put(url_for('api_relation.update_relation', relation_id=relation_id, _external=True),
                         json=payload)
        if not r:
            message = "could not update relation %s:  %s [%s]" % (relation_id, r.status_code, r.text)
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
                # don't add tags if we didn't create a dictionary entry.
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

            # FIXME - pull this out of the loop; we can update tags for multiple word_ids in a single request.
            r = requests.post(url_for('api_wordlist_tag.add_tags',
                                      wordlist_id=wordlist_id,
                                      _external=True),
                              json=payload)
            if not r:
                return render_template("error.html",
                                       message="add tags failed (wordlist_id %s):  %s [%s]" %
                                               (wordlist_id, r.text, r.status_code),
                                       status_code=r.status_code)

        target = url_for(redirect_to,
                         word=word,
                         relation_id=relation_id,
                         serialized_tag_state=tag_state_object.serialize(),
                         wordlist_id=wordlist_id)
    else:
        target = url_for(redirect_to,
                         word=word,
                         relation_id=relation_id)

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
        return redirect(url_for('dlernen.word_editor',
                                word=word,
                                serialized_tag_state=serialized_tag_state,
                                redirect_to=redirect_to,
                                _external=True))

    else:
        flash(r.text)

    return redirect(url_for('dlernen.word_editor',
                            word=word,
                            serialized_tag_state=serialized_tag_state,
                            redirect_to=redirect_to,
                            _external=True))


@bp.route('/update_words', methods=['POST'])
def bulk_add_page():
    # submitting from the add word field in the sidebar will bring us here.

    # this will update the prevailing word list with the word in the request.  if that word isn't in the dictionary,
    # redirect to the word edit page.  on submit, go to <redirect_to>.

    serialized_tag_state = request.form.get('serialized_tag_state')
    redirect_to = request.form.get('redirect_to')
    words_to_add = request.form.get('bulk_add_submit').strip().split()

    tag_state = None
    if serialized_tag_state:
        tag_state = TagState.deserialize(serialized_tag_state)

    if not words_to_add:
        if tag_state:
            return redirect(url_for(redirect_to,
                                    wordlist_id=tag_state.wordlist_id,
                                    _external=True))
        return redirect(url_for(redirect_to, _external=True))

    words_to_add = sorted(set(words_to_add))  # remove dups and sort

    # get info for all parts of speech

    word_to_pos_info = {}
    for w in words_to_add:
        r = requests.get(url_for('api_pos.get_pos_for_word', word=w, _external=True))
        if not r:
            return render_template("error.html",
                                   message=r.text,
                                   status_code=r.status_code)
        pos_info = r.json()
        word_to_pos_info[w] = pos_info

    # turn the word_to_pos_info into something we can render
    # need label, field name, field value

    word_to_form_data = {}
    for w, pos_info in word_to_pos_info.items():
        a = []
        for p in pos_info:
            # dig the definition out of the pos_info.
            defn_attr = list(filter(lambda x: x['attrkey'] == 'definition', p[ATTRIBUTES]))
            if not defn_attr:
                # 'definition' *should* be a defined attribute for every part of speech, but let's be careful anyway.
                continue

            defn_attr = defn_attr[0]
            field_value = defn_attr['attrvalue'] if defn_attr['attrvalue'] is not None else ''
            field_label = p['pos_name']
            field_name_parts = ['word', w, p['pos_id'], defn_attr['attribute_id']]
            if p['word_id']:
                field_name_parts.append(p['word_id'])
            field_name_parts = list(map(str, field_name_parts))  # convert to str so join won't choke
            field_name = '-'.join(field_name_parts)

            a.append({
                'label': field_label,
                'value': field_value,
                'name': field_name
            })
        word_to_form_data[w] = a

    return render_template("bulk_add.html",
                           redirect_to=redirect_to,
                           tag_state=tag_state,
                           word_to_form_data=word_to_form_data)


@bp.route('/bulk_add', methods=['POST'])
def bulk_add_submit():
    # hitting the submit button in the bulk add page brings us here.

    # NB - this is pretty close to the algorithm used in word_editor_submit, but not close enough that we can
    #  actually reuse code.  the form fields in the word-edit form and this form are different.  the words are
    #  embedded in the field names here.  we can't do that in the other form because of the possibility that we would
    #  change the spelling of the word there.

    # TODO - tags
    # TODO - noun genders
    # TODO - checkboxes to indicate which words we will/will not add.

    # rules of the game:
    #
    # - do not add/update anything if no definition is given.
    # - clearing the definition for an existing word will cause its attributes to be deleted.
    # - noun gender must be set if its definition is given.

    # this will word by dropping all the definitions for extant words, then adding them back with what we pull from
    # the form.  even if the definition is unchanged.  clunky but better than diffing.

    serialized_tag_state = request.form.get('serialized_tag_state')
    redirect_to = request.form.get('redirect_to')

    wordlist_id = None
    tag_state_object = None
    if serialized_tag_state:
        # in case we added a new tag while editing the word
        tag_state_object = TagState.deserialize(serialized_tag_state)
        tag_state_object.update()
        wordlist_id = tag_state_object.wordlist_id
    print("########################## %s" % wordlist_id)
    # maps word_ids to WORD_UPDATE_PAYLOAD_SCHEMA docs.  what an update payload looks like:
    #
    # payload for deleting an attribute value:
    # {
    #     ATTRIBUTES: [
    #         {
    #             'attribute_id': attr_id
    #         }
    #     ]
    # }
    #
    # payload for updating an attribute value:
    # {
    #     ATTRIBUTES: [
    #         {
    #             'attrvalue': attrvalue,
    #             'attribute_id': attr_id
    #         }
    #     ]
    # }

    word_ids_to_update_payloads = {}
    word_ids_to_delete_payloads = {}

    # maps (word, pos_id) pairs to WORD_ADD_PAYLOAD_SCHEMA docs
    word_pos_to_add_payloads = {}

    # mapping of (word, pos_id) to word_id.  this will be used for extant words as well as new ones we create.
    word_pos_to_word_id = {}

    for field_name, value_unstripped in request.form.items():
        parts = field_name.split('-')
        if parts[0] != 'word':
            continue

        value = value_unstripped.strip()
        word = parts[1]
        pos_id = int(parts[2])
        attribute_id = int(parts[3])
        word_id = int(parts[4]) if len(parts) > 4 else None

        t = (word, pos_id)
        if word_id:
            word_pos_to_word_id[t] = word_id

            if word_id not in word_ids_to_delete_payloads:
                word_ids_to_delete_payloads[word_id] = {
                    ATTRIBUTES: []
                }
            payload = word_ids_to_delete_payloads[word_id]
            payload[ATTRIBUTES].append(
                {
                    'attribute_id': attribute_id
                }
            )

            if word_id not in word_ids_to_update_payloads:
                word_ids_to_update_payloads[word_id] = {
                    ATTRIBUTES: []
                }
            payload = word_ids_to_update_payloads[word_id]
            if value:
                payload[ATTRIBUTES].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

        else:
            if t not in word_pos_to_add_payloads:
                word_pos_to_add_payloads[t] = {
                    'word': word,
                    'pos_id': t[1],
                    ATTRIBUTES: []
                }
            payload = word_pos_to_add_payloads[t]
            if value:
                payload[ATTRIBUTES].append(
                    {
                        'attribute_id': attribute_id,
                        'attrvalue': value
                    }
                )

    # get rid of payloads with empty attribute lists
    # FIXME - need to refine this to also drop add payloads for nouns where gender and defn are not both
    #  present.
    word_pos_to_add_payloads = {k: v for k, v in word_pos_to_add_payloads.items()
                                if len(v[ATTRIBUTES]) > 0}
    word_ids_to_update_payloads = {k: v for k, v in word_ids_to_update_payloads.items()
                                   if len(v[ATTRIBUTES]) > 0}

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
        word, pos_id = t
        url = url_for('api_word.add_word', _external=True)
        r = requests.post(url, json=payload)
        if not r:
            message = "could not add word %s [%s]:  %s" % (word, r.status_code, r.text)
            return render_template("error.html",
                                   message=message,
                                   status_code=r.status_code)

        obj = r.json()
        word_pos_to_word_id[(word, pos_id)] = obj['word_id']

    # this is *all* of the words in the bulk add operation, both extant and newly-created.
    word_ids = list(word_pos_to_word_id.values())

    # if there is a wordlist_id, add all the word ids to the wordlist.  just add all of them; adding a word id that
    # is already there does nothing.

    if wordlist_id:
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

    if False and wordlist_id:
        # first, drop all the tags for each word_id in the wordlist.

        for word_id in word_pos_to_word_id.values():
            r = requests.delete(url_for('api_wordlist_tag.delete_tags_for_word_id',
                                        word_id=word_id,
                                        wordlist_id=wordlist_id,
                                        _external=True))
            if not r:
                message = "could not delete tags %s:  %s [%s] (shouldn't get a 400 here)" % (wordlist_id,
                                                                                             r.status_code,
                                                                                             r.text)
                return render_template("error.html",
                                       message=message,
                                       status_code=r.status_code)

        # next, add back the tags that we pull from the form.

        payload = []
        for field_name, value_unstripped in request.form.items():
            parts = field_name.split('-')

            value = value_unstripped.strip()
            word = parts[1]
            pos_id = int(parts[2])

            if parts[0] != 'tag':
                continue

            if (word, pos_id) not in word_pos_to_word_id:
                # don't add tags if we didn't create a dictionary entry.
                continue

            tag_str = value
            tags = tag_str.split()
            if not tags:
                continue

            payload.append(
                {
                    'word_id': word_pos_to_word_id[(word, pos_id)],
                    'tags': tags
                }
            )

        if payload:
            r = requests.post(url_for('api_wordlist_tag.add_tags',
                                      wordlist_id=wordlist_id,
                                      _external=True),
                              json=payload)
            if not r:
                return render_template("error.html",
                                       message="add tags failed (wordlist_id %s):  %s [%s]" %
                                               (wordlist_id, r.text, r.status_code),
                                       status_code=r.status_code)

    # wrap up by redirecting to the right place ...
    return redirect(url_for(redirect_to,
                            serialized_tag_state=serialized_tag_state,
                            wordlist_id=wordlist_id,
                            _external=True))


@bp.route('/search_results', methods=['POST'])
def search_results_submit():
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
