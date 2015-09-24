\W

select
	pos.name,
	pos.id pos_id,
	v.attribute_id,
	a.attrkey,
	wa.word_id,
	wa.value
from words_x_attributes_v v   -- pos_id, word_id, attribute_id
inner join pos on pos.id = v.pos_id
inner join attribute a on a.id = v.attribute_id
inner join word on word.id = v.word_id
left join word_attribute wa on v.word_id = wa.word_id and v.attribute_id = wa.attribute_id
where pos.name = 'noun'
and word.word = 'essen'
order by v.word_id, v.attribute_id
;
