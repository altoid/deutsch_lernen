import pickle
import base64
import requests
from flask import url_for


class TagState(object):
    def __init__(self, wordlist_id=None, tags_to_states=None, tags=None):
        self.wordlist_id = wordlist_id

        if tags_to_states:
            self.tags_to_states = tags_to_states
        else:
            self.tags_to_states = dict()

        if tags:
            self.tags = tags
        else:
            self.tags = []

        if not tags:
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


