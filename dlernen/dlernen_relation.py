from flask import Blueprint, request, render_template, redirect, url_for
import requests
import json
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
    payload = {
        'word_ids': [word_id]
    }
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


@bp.route('/update_description', methods=['POST'])
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


@bp.route('/update_notes', methods=['POST'])
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

