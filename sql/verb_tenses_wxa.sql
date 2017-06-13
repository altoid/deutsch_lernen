/*
word pos pos_form attribute word_attribute

words_x_attributes_v (pos_id, attribute_id, word_id)

*/

-- explain
select
def.word		infinitive,
-- def.attrvalue	definition,
fps.attrvalue	first_person_singular,
sps.attrvalue	second_person_singular,
tps.attrvalue	third_person_singular,
-- fpp.attrvalue	first_person_plural,
-- spp.attrvalue	second_person_plural,
tpp.attrvalue	third_person_plural,
tpt.attrvalue	third_person_past,
pp.attrvalue	past_participle,
1
from
(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'definition'
) def

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'first_person_singular'
) fps

on fps.word_id = def.word_id

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'second_person_singular'
) sps

on sps.word_id = def.word_id

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'third_person_singular'
) tps

on tps.word_id = def.word_id

-- left join
-- 
-- (
-- select
-- 		w.id word_id,
-- 		w.word,
-- 		wa.value		attrvalue
-- from
-- 		words_x_attributes_v wav
-- inner join pos on pos.id = wav.pos_id
-- inner join attribute a on a.id = wav.attribute_id
-- inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
-- inner join word w on w.id = wav.word_id and w.id = wa.word_id
-- where
-- pos.name = 'Verb'
-- and a.attrkey = 'first_person_plural'
-- ) fpp
-- 
-- on fpp.word_id = def.word_id
-- 
-- left join
-- 
-- (
-- select
-- 		w.id word_id,
-- 		w.word,
-- 		wa.value		attrvalue
-- from
-- 		words_x_attributes_v wav
-- inner join pos on pos.id = wav.pos_id
-- inner join attribute a on a.id = wav.attribute_id
-- inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
-- inner join word w on w.id = wav.word_id and w.id = wa.word_id
-- where
-- pos.name = 'Verb'
-- and a.attrkey = 'second_person_plural'
-- ) spp
-- 
-- on spp.word_id = def.word_id

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'third_person_plural'
) tpp

on tpp.word_id = def.word_id

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'third_person_past'
) tpt

on tpt.word_id = def.word_id

left join

(
select
		w.id word_id,
		w.word,
		wa.value		attrvalue
from
		words_x_attributes_v wav
inner join pos on pos.id = wav.pos_id
inner join attribute a on a.id = wav.attribute_id
inner join word_attribute wa on wa.attribute_id = wav.attribute_id and wa.word_id = wav.word_id
inner join word w on w.id = wav.word_id and w.id = wa.word_id
where
pos.name = 'Verb'
and a.attrkey = 'past_participle'
) pp

on pp.word_id = def.word_id

;

/*
select 
-- def.word_id,
def.word infinitive,

fps.attrvalue first_person_singular,
 sps.attrvalue second_person_singular,
tps.attrvalue third_person_singular,

 fpp.attrvalue first_person_plural,
 spp.attrvalue second_person_plural,
 tpp.attrvalue third_person_plural,

tpt.attrvalue third_person_past,
pp.attrvalue past_participle,
def.attrvalue definition

from
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'definition'
) def 

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'first_person_singular'
) fps
on fps.word_id = def.word_id

 left join 
 (
 select
 word_id,
 word,
 attrvalue
 from mashup
 where pos_name = 'verb'
 and attrkey = 'second_person_singular'
 ) sps
 on sps.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'third_person_singular'
) tps
on tps.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'first_person_plural'
) fpp
on fpp.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'second_person_plural'
) spp
on spp.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'third_person_plural'
) tpp
on tpp.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'third_person_past'
) tpt
on tpt.word_id = def.word_id

left join 
(
select
word_id,
word,
attrvalue
from mashup
where pos_name = 'verb'
and attrkey = 'past_participle'
) pp
on pp.word_id = def.word_id
;
*/
