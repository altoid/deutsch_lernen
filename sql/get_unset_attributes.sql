-- given a part of speech and an attribute, get all
-- words for which that attribute is unset.

/*
-- this view is a cartesian product of the words and all of the
-- attributes they have

drop view if exists words_x_attributes;
create view words_x_attributes
as
select pf.pos_id, pf.attribute_id, w.id word_id
from pos_form pf inner join word w on pf.pos_id = w.pos_id
;
*/

--
select a.attrkey, x.*, wa.*, w.word
from words_x_attributes x 
inner join pos on pos.id = x.pos_id
inner join attribute a on a.id = x.attribute_id
inner join word w on w.id = x.word_id
left join word_attribute wa on x.attribute_id = wa.attribute_id 
                           and x.word_id = wa.word_id

where pos.name = 'verb'
and a.attrkey = 'first_person_singular'
and wa.value is null
;
