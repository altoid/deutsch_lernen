import pickle
import base64
import requests
from flask import url_for


class TagState(object):
    def __init__(self, wordlist_id):

        # list_type is an unpleasant but necessary encroachment.  list_type is needed in order to render
        # the Editor item in the sidebar menu, because it is a function of list type:  we don't enable editing of
        # smart lists.  if we don't have the list_type in this class, then we need to pass both a tag state object
        # and a wordlist object, which is extremely messy:  in each template we would have to check that the tag
        # state and the word list both exist, have matching wordlist_ids, etc.  to avoid all this we put list_type
        # into the tag state and derive it from wordlist_id.
        #
        # will need a serious re-think if we ever need to put additional crap in here.
        #

        self.wordlist_id = wordlist_id
        self.list_type = None
        self.tags_to_states = dict()
        self.tags = []

        self.update()

    def update(self):
        current_tags = set(self.tags_to_states.keys())
        r = requests.get(url_for('api_wordlist_tag.get_all_tags',
                                 wordlist_id=self.wordlist_id,
                                 _external=True))
        obj = r.json()
        tags = obj['tags']
        self.tags = sorted(tags)

        tags_set = set(tags)
        keys_to_remove = current_tags - tags_set
        keys_to_add = tags_set - current_tags
        for k in keys_to_remove:
            del self.tags_to_states[k]
        for k in keys_to_add:
            self.tags_to_states[k] = False  # unchecked

        # set list_type
        r = requests.get(url_for('api_wordlist.get_metadata',
                                 wordlist_id=self.wordlist_id,
                                 _external=True))
        obj = r.json()
        self.list_type = obj['list_type']

    def tag_state(self):
        # returns tuple of (<tag>, state), for rendering, in sorted order
        states = [self.tags_to_states[k] for k in self.tags]
        return list(zip(self.tags, states))

    def selected_tags(self):
        return list(filter(lambda x: self.tags_to_states[x], self.tags))

    def clear(self):
        for k in self.tags_to_states.keys():
            self.tags_to_states[k] = False  # unchecked

    def set_tags(self, tags):
        for t in tags:
            if t in self.tags_to_states:
                self.tags_to_states[t] = True  # checked

    @staticmethod
    def deserialize(blob):
        deserialized_thing = pickle.loads(base64.urlsafe_b64decode(blob))
        return deserialized_thing

    def serialize(self):
        ser_bytes = pickle.dumps(self)
        return base64.urlsafe_b64encode(ser_bytes).decode("utf-8")


