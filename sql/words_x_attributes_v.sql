create or replace view words_x_attributes_v as
select
	w.pos_id,
	w.id word_id,
	nwa.attribute_id,
	nwa.attrvalue_id
from word w
join word_attribute nwa on w.id = nwa.word_id
;
