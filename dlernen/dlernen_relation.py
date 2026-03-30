from flask import Blueprint, request, render_template, redirect, url_for, flash
import requests
from dlernen.tagstate import TagState

from pprint import pprint

bp = Blueprint('dlernen_relation', __name__, url_prefix='/dlernen/relation')


@bp.route('/editor/<int:relation_id>')
def relation_editor(relation_id):
    url = url_for('api_relation.get_relation', relation_id=relation_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    relation = r.json()

    serialized_tag_state = request.args.get('serialized_tag_state')
    if serialized_tag_state:
        return render_template('relation_editor.html',
                               tag_state=TagState.deserialize(serialized_tag_state),
                               relation=relation)

    return render_template('relation_editor.html',
                           relation=relation)


@bp.route('', methods=['POST'])
def create_relation():
    wordlist_id = request.form.get('wordlist_id', type=int)
    word_id = request.form.get('word_id', type=int)
    serialized_tag_state = request.form.get('serialized_tag_state')

    # create a new relation with this word
    payload = {}

    if word_id:
        payload['word_ids'] = [word_id]

    r = requests.post(url_for('api_relation.create_relation', _external=True), json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    relation = r.json()
    return redirect(url_for('dlernen_relation.relation_editor',
                            wordlist_id=wordlist_id,
                            relation_id=relation['relation_id'],
                            serialized_tag_state=serialized_tag_state))


@bp.route('/description', methods=['POST'])
def update_description():
    wordlist_id = request.form.get('wordlist_id', type=int)
    relation_id = request.form.get('relation_id', type=int)
    serialized_tag_state = request.form.get('serialized_tag_state')
    description = request.form.get('description')

    payload = {
        'description': description
    }
    r = requests.put(url_for('api_relation.update_relation', relation_id=relation_id, _external=True), json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    return redirect(url_for('dlernen_relation.relation_editor',
                            wordlist_id=wordlist_id,
                            relation_id=relation_id,
                            serialized_tag_state=serialized_tag_state,
                            _external=True))


@bp.route('/notes', methods=['POST'])
def update_notes():
    wordlist_id = request.form.get('wordlist_id', type=int)
    relation_id = request.form.get('relation_id', type=int)
    serialized_tag_state = request.form.get('serialized_tag_state')
    notes = request.form.get('notes')

    payload = {
        'notes': notes
    }
    r = requests.put(url_for('api_relation.update_relation', relation_id=relation_id, _external=True), json=payload)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    return redirect(url_for('dlernen_relation.relation_editor',
                            wordlist_id=wordlist_id,
                            relation_id=relation_id,
                            serialized_tag_state=serialized_tag_state,
                            _external=True))


@bp.route('/words', methods=['POST'])
def update_words():
    # submitting from the add word field will bring us here.

    # this will add the word to the relation.  if that word isn't in the dictionary,
    # redirect to the word edit page.  on submit, go to <redirect_to>.

    serialized_tag_state = request.form.get('serialized_tag_state')
    relation_id = request.form.get('relation_id')
    button = request.form.get('submit')

    tag_state = TagState.deserialize(serialized_tag_state)
    redirect_to = 'dlernen_relation.relation_editor'

    if button.startswith('Delete'):
        # the checkboxes are called 'removing'

        word_ids = list(map(int, request.form.getlist('removing')))
        if word_ids:
            payload = {
                'word_ids': word_ids
            }
            r = requests.put(url_for('api_relation.delete_from_relation',
                                     relation_id=relation_id,
                                     _external=True),
                             json=payload)
            if not r:
                return render_template("error.html",
                                       message=r.text,
                                       status_code=r.status_code)

    elif button.startswith('Add'):
        word = request.form.get('add_word').strip()
        if word:
            url = url_for('api_word.get_word', word=word, _external=True)
            r = requests.get(url)
            if r:
                obj = r.json()
                word_ids = [x['word_id'] for x in obj]
                payload = {
                    "word_ids": word_ids
                }

                url = url_for('api_relation.update_relation', relation_id=relation_id, _external=True)
                r2 = requests.put(url, json=payload)
                if not r2:
                    flash(r2.text)
            elif r.status_code == 404:
                return redirect(url_for('dlernen.edit_word_form',
                                        word=word,
                                        relation_id=relation_id,
                                        wordlist_id=tag_state.wordlist_id,
                                        serialized_tag_state=serialized_tag_state,
                                        redirect_to=redirect_to,
                                        _external=True))
            else:
                flash(r.text)

    return redirect(url_for(redirect_to,
                            relation_id=relation_id,
                            serialized_tag_state=serialized_tag_state))
