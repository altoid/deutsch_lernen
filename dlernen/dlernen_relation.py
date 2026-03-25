from flask import Blueprint, request, render_template, redirect, url_for
import requests
import json
from dlernen.tagstate import TagState

from pprint import pprint

bp = Blueprint('dlernen_relation', __name__, url_prefix='/dlernen/relation')


@bp.route('/editor/<int:relation_id>')
def relation_editor(relation_id):
    wordlist_id = request.args.get('wordlist_id')
    url = url_for('api_wordlist.get_wordlist', wordlist_id=wordlist_id, _external=True)
    r = requests.get(url)
    if not r:
        return render_template("error.html",
                               message=r.text,
                               status_code=r.status_code)

    wordlist = r.json()
    return render_template('relation_editor.html',
                           serialized_tag_state=request.args.get('serialized_tag_state'),
                           wordlist=wordlist,
                           relation_id=relation_id)


@bp.route('', methods=['POST'])
def create_relation():
    wordlist_id = request.form.get('wordlist_id')
    word_id = request.form.get('word_id')
    serialized_tag_state = request.form.get('serialized_tag_state')

    return redirect(url_for('dlernen.relation_editor',
                            word_id=word_id,
                            wordlist_id=wordlist_id,
                            relation_id=0,
                            serialized_tag_state=serialized_tag_state))

