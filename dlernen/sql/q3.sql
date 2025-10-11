with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quizkey = 'plurals'
),
given_words as (
select id word_id from word
where id in (3243,3416)
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

select
'QUERY1' qname,
ta.quiz_id,
ta.attribute_id,
ta.attrkey,
ta.word_id,
ta.word,
ta.attrvalue,
ifnull(v.presentation_count, 0) presentation_count,
ifnull(v.correct_count, 0) correct_count,
v.last_presentation
from testable_attrs_and_values ta
left join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where ifnull(presentation_count, 0) <= 5

;
