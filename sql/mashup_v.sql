/*
select
	pf.pos_id AS pos_id,
	pf.attribute_id AS attribute_id,
	w.id AS word_id
from pos_form pf
join word w on pf.pos_id = w.pos_id
;

*/
/*
create or replace view new_words_x_attributes_v as
select
	w.pos_id,
	w.id word_id,
	nwa.attribute_id,
	nwa.attrvalue_id
from word w
join new_word_attribute nwa on w.id = nwa.word_id
;
*/
-- mashup_v

create or replace view mashup_v as
select
	w.id AS word_id,
	w.word AS word,
	w.added AS added,
	pos.id AS pos_id,
	pos.name AS pos_name,
	a.id AS attribute_id,
	a.attrkey AS attrkey,
	pf.sort_order AS sort_order,
	av.id as attrvalue_id,
	av.attrvalue AS attrvalue

from pos
join pos_form pf on pos.id = pf.pos_id
join attribute a on a.id = pf.attribute_id
left join word w on w.pos_id = pos.id
left join words_x_attributes_v v on v.pos_id = pos.id and v.attribute_id = a.id and v.word_id = w.id
left join word_attribute wa on wa.attribute_id = v.attribute_id and wa.word_id = v.word_id
left join attrvalue av on wa.attrvalue_id = av.id

;
