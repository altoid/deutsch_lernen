select
	p.name,
	w.word,
	a.attrkey,
	wa.value,
	1
from
	pos p,
	word w,
	attribute a,
	word_attribute wa,
	words_x_attributes_v v
where
	v.pos_id = p.id	and
	v.attribute_id = a.id	and
	v.word_id = w.id and
	wa.attribute_id = v.attribute_id	and
	wa.word_id = w.id and
	w.word = 'ausstrahlen'	and
	1
;

