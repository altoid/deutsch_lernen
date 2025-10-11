with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quizkey = 'plurals'
),
given_words as (
select id word_id from word
where id in (112,2052,2695,3529,4341)
),
testable_attributes as (
select * from
attrs_for_quiz,
given_words
),
testable_attrs_and_values as (
select ta.*,
mashup_v.word, mashup_v.attrvalue
from testable_attributes ta
inner join mashup_v on ta.word_id = mashup_v.word_id and ta.attribute_id = mashup_v.attribute_id
)

select * from testable_attrs_and_values
where word_id not in (
    select word_id from testable_attrs_and_values
    where attrvalue is null
    )
;
