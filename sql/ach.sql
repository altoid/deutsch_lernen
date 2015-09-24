
-- get all the attributes associated with nouns

select * from pos, pos_form, attribute where pos.id = pos_form.pos_id
  and pos_form.attribute_id = attribute.id and pos.name = 'Noun'
;

-- get the word  id for a single article/word

select w.id from pos, attribute a, word w, word_attribute wa where a.attrkey = 'article' and    
a.id = wa.attribute_id and wa.value = 'die' and
 pos.name = 'Noun' and pos.id = w.pos_id and w.word = 'blume' and
 w.id = wa.word_id
;

-- want all attribute values for this word, showing nulls for unset values

select pos.name, pos_form.*, a.attrkey, wa.word_id, wa.value from pos
inner join pos_form on pos.id = pos_form.pos_id
inner join attribute a on pos_form.attribute_id = a.id
left join word_attribute wa on wa.attribute_id = a.id and word_id = 
(
select w.id from pos pos2, attribute a, word w, word_attribute wa 
where a.attrkey = 'article' and    
 a.id = wa.attribute_id and 
 wa.value = 'die' and
 pos2.name = pos.name and
 pos.id = w.pos_id and
 w.word = 'blume' and
 w.id = wa.word_id
)
where
 pos.name = 'Noun'
;
