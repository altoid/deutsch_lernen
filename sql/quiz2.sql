use deutsch;

with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = 'third_person_past'
)
/*
,
given_words as (
select id word_id from word
where id in ({word_ids})
),
testable_attributes as (
select * from
attrs_for_quiz,
given_words
),
attrs_and_values as (
select ta.*,
mashup_v.word, mashup_v.attrvalue, mashup_v.attrkey
from testable_attributes ta
inner join mashup_v on ta.word_id = mashup_v.word_id and ta.attribute_id = mashup_v.attribute_id
),
testable_attrs_and_values as (
select * from attrs_and_values	
where word_id not in (
    select word_id from attrs_and_values
    where attrvalue	is null
    )
)
*/

select a.*, m.attrkey, m.word_id, m.word, m.attrvalue
from attrs_for_quiz a
inner join mashup_v m
on a.attribute_id = m.attribute_id
where attrvalue is not null
order by rand()

limit 11

;
