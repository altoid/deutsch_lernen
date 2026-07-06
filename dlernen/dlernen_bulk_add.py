from flask import Blueprint, request, render_template, redirect, url_for, flash, abort, current_app
import requests

from dlernen.tagstate import TagState
from dlernen.dlernen_json_schema import ATTRIBUTES

from pprint import pprint, pformat

bp = Blueprint('dlernen_bulk_add', __name__, url_prefix='/dlernen/bulk_add')

ATTRIBUTE_FIELD_PREFIX = 'attr'
TAG_FIELD_PREFIX = 'tag'


def get_bulk_add_form_data(raw_list, wordlist_id=None):
    # returns 2 dictionaries:
    #
    # 1.  mapping of each unique word in the raw list to a dict giving the label and field name
    #     for each text field in the bulk-add page.
    # 2.  mapping of field names to field values.

    words_to_add = raw_list.strip().split()
    words_to_add = sorted(set(words_to_add))  # remove dups and sort

    # get info for all parts of speech
    word_to_pos_info = {}
    for w in words_to_add:
        r = requests.get(url_for('api_pos.get_pos_for_word', word=w, _external=True))
        if not r:
            abort(r.status_code, response=r)
        pos_info = r.json()
        word_to_pos_info[w] = pos_info

    # turn the word_to_pos_info into something we can render
    # need label, field name, field value
    word_to_form_data = {}
    field_names_to_field_values = {}

    for w, pos_info in word_to_pos_info.items():
        a = []
        for p in pos_info:
            # dig the definition out of the pos_info.
            attrs = list(filter(lambda x: x['attrkey'] in ['definition', 'article'], p[ATTRIBUTES]))
            for attr in attrs:
                attr_field_value = attr['attrvalue'] if attr['attrvalue'] is not None else ''
                tag_field_value = ''
                tag_field_name = None
                label = p['pos_name']
                common_field_parts = [w, p['pos_name'], attr['attrkey']]
                if p['word_id']:
                    common_field_parts.append(p['word_id'])

                common_field_parts = list(map(str, common_field_parts))  # convert to str so join won't choke

                attr_field_name = '-'.join([ATTRIBUTE_FIELD_PREFIX] + common_field_parts)
                field_names_to_field_values[attr_field_name] = attr_field_value

                if p['word_id'] and wordlist_id:
                    r = requests.get(url_for('api_wordlist_tag.get_tags',
                                             word_id=p['word_id'],
                                             wordlist_id=wordlist_id,
                                             _external=True))

                    if r:
                        tags_obj = r.json()
                        tag_field_value = ' '.join(tags_obj['tags'])
                    elif r.status_code == 404:
                        pass  # we don't care.
                    else:
                        # other problems, we care about.
                        abort(r.status_code, response=r)

                if attr['attrkey'] == 'definition':
                    tag_field_name = '-'.join([TAG_FIELD_PREFIX] + common_field_parts)
                    field_names_to_field_values[tag_field_name] = tag_field_value

                a.append({
                    'label': label,
                    'attr_field_name': attr_field_name,
                    'tag_field_name': tag_field_name,
                    'attribute': attr['attrkey']
                })

                # tag_field_name will be None for articles, tag+word+pos_name+attrkey for definitions.  that way
                # when we have a tag field name, we will also have an attr field name (for definitions) and we will
                # know what the attr field name is:  the two fields will be the same except for the FIELD_PREFIX.

        word_to_form_data[w] = a

    return word_to_form_data, field_names_to_field_values


def update_tags(word_pos_to_word_id, wordlist_id):
    # first, drop all the tags for each word_id in the wordlist.
    for word_id in word_pos_to_word_id.values():
        r = requests.delete(url_for('api_wordlist_tag.delete_tags_for_word_id',
                                    word_id=word_id,
                                    wordlist_id=wordlist_id,
                                    _external=True))
        if not r:
            message = "could not delete tags for wordlist %s (shouldn't get a 400 here)" % wordlist_id
            abort(r.status_code, message=message, response=r)
    # next, add back the tags that we pull from the form.
    payload = []
    for field_name, value_unstripped in request.form.items():
        parts = field_name.split('-')

        if parts[0] != TAG_FIELD_PREFIX:
            continue

        word = parts[1]
        pos_name = parts[2]

        if (word, pos_name) not in word_pos_to_word_id:
            # don't add tags if we didn't create a dictionary entry.
            continue

        tags = value_unstripped.strip().split()
        if not tags:
            continue

        payload.append(
            {
                'word_id': word_pos_to_word_id[(word, pos_name)],
                'tags': tags
            }
        )
    if payload:
        r = requests.post(url_for('api_wordlist_tag.add_tags',
                                  wordlist_id=wordlist_id,
                                  _external=True),
                          json=payload)
        if not r:
            message = "add tags failed for wordlist %s" % wordlist_id
            abort(r.status_code, message=message, response=r)


@bp.route('/editor', methods=['POST'])
def editor_page():
    # submitting from the add word field in the sidebar will bring us here.

    # this will update the prevailing word list with the word in the request.  if that word isn't in the dictionary,
    # redirect to the word edit page.  on submit, go to <redirect_to>.

    serialized_tag_state = request.form.get('serialized_tag_state')
    redirect_to = request.form.get('redirect_to')

    tag_state = None
    wordlist_id = None
    if serialized_tag_state:
        tag_state = TagState.deserialize(serialized_tag_state)
        wordlist_id = tag_state.wordlist_id

    raw_list = request.form.get('bulk_add_submit', '')
    word_to_form_data, field_names_to_field_values = get_bulk_add_form_data(raw_list, wordlist_id=wordlist_id)

    if not word_to_form_data:
        return redirect(url_for(redirect_to,
                                wordlist_id=wordlist_id,
                                _external=True))

    return render_template("bulk_add.html",
                           redirect_to=redirect_to,
                           tag_state=tag_state,
                           raw_list=raw_list,
                           word_to_form_data=word_to_form_data,
                           field_names_to_field_values=field_names_to_field_values)


@bp.route('/submit', methods=['POST'])
def bulk_add_submit():
    # hitting the submit button in the bulk add page brings us here.

    # this is pretty close to the algorithm used in word_editor_submit, but not close enough that we can
    # actually reuse code.  the form fields in the word-edit form and this form are different.  the words are
    # embedded in the field names here.  we can't do that in the other form because of the possibility that we would
    # change the spelling of the word there.

    # rules of the game:
    #
    # - do not add/update anything if no definition is given.
    # - noun gender must be set if its definition is given.

    # this will work by dropping all the definitions for extant words, then adding them back with what we pull from
    # the form.  even if the definition is unchanged.  clunky but better than diffing.

    posname_enum = current_app.extensions.get('POSName')
    serialized_tag_state = request.form.get('serialized_tag_state')
    redirect_to = request.form.get('redirect_to')

    wordlist_id = None
    tag_state_object = None
    if serialized_tag_state:
        # in case we added a new tag while editing the word
        tag_state_object = TagState.deserialize(serialized_tag_state)
        tag_state_object.update()
        wordlist_id = tag_state_object.wordlist_id

    # these map word_ids to WORD_UPDATE_PAYLOAD_SCHEMA docs.

    word_ids_to_update_payloads = {}
    word_ids_to_delete_payloads = {}

    # maps (word, pos_name) pairs to WORD_ADD_PAYLOAD_SCHEMA docs
    word_pos_to_add_payloads = {}

    # mapping of (word, pos_name) to word_id.  this will be used for extant words as well as new ones we create.
    word_pos_to_word_id = {}

    for field_name, value_unstripped in request.form.items():
        parts = field_name.split('-')
        if parts[0] != ATTRIBUTE_FIELD_PREFIX:
            continue

        value = value_unstripped.strip()
        word = parts[1]
        pos_name = parts[2]
        attrkey = parts[3]
        word_id = int(parts[4]) if len(parts) > 4 else None

        t = (word, pos_name)
        if word_id:
            word_pos_to_word_id[t] = word_id

            if word_id not in word_ids_to_delete_payloads:
                word_ids_to_delete_payloads[word_id] = {
                    ATTRIBUTES: []
                }
            payload = word_ids_to_delete_payloads[word_id]
            payload[ATTRIBUTES].append(
                {
                    'attrkey': attrkey
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
                        'attrkey': attrkey,
                        'attrvalue': value
                    }
                )

        else:
            if t not in word_pos_to_add_payloads:
                word_pos_to_add_payloads[t] = {
                    'word': word,
                    'pos_name': t[1],
                    ATTRIBUTES: []
                }
            payload = word_pos_to_add_payloads[t]
            if value:
                payload[ATTRIBUTES].append(
                    {
                        'attrkey': attrkey,
                        'attrvalue': value
                    }
                )

    # get rid of payloads with empty attribute lists
    word_pos_to_add_payloads = {k: v for k, v in word_pos_to_add_payloads.items()
                                if len(v[ATTRIBUTES]) > 0}
    word_ids_to_update_payloads = {k: v for k, v in word_ids_to_update_payloads.items()
                                   if len(v[ATTRIBUTES]) > 0}

    # check:  if a noun is given with only one of definition or article, flash message and return to page.
    messages = []
    nouns_missing_attributes = []
    for k, payload in word_pos_to_add_payloads.items():
        word, pos_name = k
        if pos_name != posname_enum.NOUN:
            continue

        article_attr = list(filter(lambda x: x['attrkey'] == 1, payload[ATTRIBUTES]))  # attr id for article
        if not article_attr:
            nouns_missing_attributes.append(word)
            continue

        defn_attr = list(filter(lambda x: x['attrkey'] == 5, payload[ATTRIBUTES]))  # attr id for defn
        if not defn_attr:
            nouns_missing_attributes.append(word)
            continue

    if nouns_missing_attributes:
        message = 'definition or article not given for these nouns:  %s' % ', '.join(nouns_missing_attributes)
        flash(message)
        messages.append(message)

    # check:  if we have specified tags for a word but not a definition, flash message and return to page.
    tags_but_no_defns = set()
    for tag_field_name, value_unstripped in request.form.items():
        parts = tag_field_name.split('-')
        if parts[0] != TAG_FIELD_PREFIX:
            continue

        word = parts[1]

        # construct corresponding attribute field name
        attr_field_name = '-'.join([ATTRIBUTE_FIELD_PREFIX] + parts[1:])

        defn = request.form.get(attr_field_name)
        tag_str = request.form.get(tag_field_name)

        if tag_str and not defn:
            tags_but_no_defns.add(word)

    if tags_but_no_defns:
        message = 'tags but no definitions for these words:  %s' % ', '.join(tags_but_no_defns)
        flash(message)
        messages.append(message)

    if messages:
        # go back and try again

        raw_list = request.form.get('bulk_add_submit', '')
        word_to_form_data, _ = get_bulk_add_form_data(raw_list)

        # construct the form data from what we have already entered into the form, not from prior knowledge
        # of the words we want to bulk-add.

        field_names_to_field_values = {}
        for field_name, value_unstripped in request.form.items():
            parts = field_name.split('-')
            if parts[0] not in {ATTRIBUTE_FIELD_PREFIX, TAG_FIELD_PREFIX}:
                continue

            field_names_to_field_values[field_name] = value_unstripped

        return render_template("bulk_add.html",
                               redirect_to=redirect_to,
                               tag_state=tag_state_object,
                               raw_list=raw_list,
                               word_to_form_data=word_to_form_data,
                               field_names_to_field_values=field_names_to_field_values)

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
        word, pos_name = t
        url = url_for('api_word.add_word', _external=True)
        r = requests.post(url, json=payload)
        if not r:
            message = "could not add word %s" % word
            abort(r.status_code, message=message, response=r)

        obj = r.json()
        word_pos_to_word_id[(word, pos_name)] = obj['word_id']

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
            message = "could not update wordlist %s" % wordlist_id
            abort(r.status_code, message=message, response=r)

    # now we deal with the tags.

    if wordlist_id:
        update_tags(word_pos_to_word_id, wordlist_id)

    # wrap up by redirecting to the right place ...
    return redirect(url_for(redirect_to,
                            serialized_tag_state=serialized_tag_state,
                            wordlist_id=wordlist_id,
                            _external=True))
