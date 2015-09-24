
select pos.name, pos_form.pos_id, pos_form.attribute_id, a.attrkey, wa.word_id, wa.value from pos
inner join pos_form on pos.id = pos_form.pos_id
inner join attribute a on pos_form.attribute_id = a.id
left join word_attribute wa on wa.attribute_id = a.id and word_id = 
(
select w.id from word w
where
-- w.word = 'essen'
w.word = 'bitten'
)
where
 pos.name = 'verb'
;

--
-- all the attributes for verbs

select
	pos.*,
	pos_form.*
from
	pos
inner join
      pos_form on pos.id = pos_form.pos_id
where
	pos.name = 'verb'
;

-- word id for verb 'essen'

select
	*
from
	words_x_attributes_v v  -- pos_id, word_id, attribute_id
inner join
      pos on pos.id = v.pos_id
inner join
      word on word.id = v.word_id
where
	pos.name = 'verb'
	and word.word = 'essen'
;

       