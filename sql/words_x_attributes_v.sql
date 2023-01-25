create or replace view words_x_attributes_v as
select
	w.pos_id,
	w.id word_id,
	wa.attribute_id
from word w
join word_attribute wa on w.id = wa.word_id
;
