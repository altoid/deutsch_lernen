-- show all of the attributes for a word that are made testable by a quiz

with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
-- where quizkey = 'present_indicative'
where quizkey = 'definitions'
-- where quizkey = 'genders'
),
given_words as (
select id word_id from word
-- where id between 10 and 25
where id >= 5099
),
testable_attributes as (
select * from
attrs_for_quiz,
given_words
)

-- word has been presented 5 or fewer times (or not at all)

select
ta.quiz_id,
ta.attribute_id,
ta.word_id,
ifnull(v.presentation_count, 0) presentation_count,
ifnull(v.correct_count, 0) correct_count,
v.last_presentation
from testable_attributes ta
left join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where ifnull(presentation_count, 0) <= 5

union

-- crappy score (<= 80% in 10 or more presentations

select
ta.quiz_id,
ta.attribute_id,
ta.word_id,
ifnull(v.presentation_count, 0) presentation_count,
ifnull(v.correct_count, 0) correct_count,
v.last_presentation
from testable_attributes ta
inner join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where presentation_count >= 10
and correct_count / presentation_count <= 0.80

union

-- word hasn't been quizzed in more than 30 days

select
ta.quiz_id,
ta.attribute_id,
ta.word_id,
ifnull(v.presentation_count, 0) presentation_count,
ifnull(v.correct_count, 0) correct_count,
v.last_presentation
from testable_attributes ta
inner join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where curdate() - interval 30 day > last_presentation

;
