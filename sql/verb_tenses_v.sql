create or replace view verb_tenses_v as
select 
def.word_id,
def.word infinitive,

fps.attrvalue first_person_singular,
sps.attrvalue second_person_singular,
tps.attrvalue third_person_singular,

--  fpp.attrvalue first_person_plural,
--  spp.attrvalue second_person_plural,
-- tpp.attrvalue third_person_plural,

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

-- left join 
-- (
-- select
-- word_id,
-- word,
-- attrvalue
-- from mashup
-- where pos_name = 'verb'
-- and attrkey = 'first_person_plural'
-- ) fpp
-- on fpp.word_id = def.word_id
-- 
-- left join 
-- (
-- select
-- word_id,
-- word,
-- attrvalue
-- from mashup
-- where pos_name = 'verb'
-- and attrkey = 'second_person_plural'
-- ) spp
-- on spp.word_id = def.word_id

-- left join 
-- (
-- select
-- word_id,
-- word,
-- attrvalue
-- from mashup
-- where pos_name = 'verb'
-- and attrkey = 'third_person_plural'
-- ) tpp
-- on tpp.word_id = def.word_id

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

