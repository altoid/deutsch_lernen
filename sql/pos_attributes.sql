use deutsch;


-- word id 3588 =  'jahr', a noun

-- given a word id and a pos (id), give me all the attributes and attribute values for it.

/*
select a.attrkey, wa.value attrvalue, wa.attribute_id from
inner join pos on v.pos_id = pos.id
;
*/


select pf.attribute_id, a.attrkey, wa.value attrvalue
from pos_form pf
inner join attribute a on a.id = pf.attribute_id
left join word_attribute wa
on wa.attribute_id = pf.attribute_id
and wa.word_id = 3606
where pf.pos_id = 3
;
