-- get the dative and accusative verbs

select p.name, a.attrkey, w.word
from pos p, attribute a, word w, word_attribute wa 
where a.attrkey in ( 'dative', 'accusative') 
and a.id = wa.attribute_id  
and wa.word_id = w.id 
and w.pos_id = p.id 
and p.name = 'Verb'
order by w.word
;

