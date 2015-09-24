-- the verb must already be in the word table.

insert ignore into word_attribute (attribute_id, word_id)
select a.id, w.id
from attribute a, word w, pos p
where a.attrkey = 'dative'
and w.pos_id = p.id 
and p.name = 'Verb'
and w.word in (
     'passen',
     'gratulieren'
     )
;


