/*
+--------+---------+--------------+------------------------+---------+-------------------+---------------------+--------------------+---------------+---------------------+
| qname  | quiz_id | attribute_id | attrkey                | word_id | word              | attrvalue           | presentation_count | correct_count | last_presentation   |
+--------+---------+--------------+------------------------+---------+-------------------+---------------------+--------------------+---------------+---------------------+
| QUERY1 |       4 |            8 | third_person_singular  |    2086 | fädeln            | fädelt              |                  0 |             0 | NULL                |
| QUERY1 |       4 |            9 | first_person_plural    |    1191 | nicken            | nicken              |                  0 |             0 | NULL                |
| QUERY1 |       4 |           10 | second_person_plural   |    3175 | zerbrechen        | zerbrecht           |                  0 |             0 | NULL                |
*/

with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = 'present_indicative'
),
testable_attrs_and_values as (
select a.*, m.attrkey, m.word_id, m.word, m.attrvalue
from attrs_for_quiz a
inner join mashup_v m
on a.attribute_id = m.attribute_id
-- inner join wordlist_known_word wkw on m.word_id = wkw.word_id
-- where attrvalue is not null
-- and wkw.wordlist_id in (32)
),
q1 as
(
-- word has been presented 5 or fewer times (or not at all)
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
),
q2 as
(
-- crappy score (<= 80% in 10 or more presentations
select
'QUERY2' qname,
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
inner join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where presentation_count >= 10
and correct_count / presentation_count <= 0.80
),
q3 as
(
-- word hasn't been quizzed in more than 30 days
select
'QUERY3' qname,
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
inner join quiz_v v
on ta.word_id = v.word_id
and ta.quiz_id = v.quiz_id
and ta.attribute_id = v.attribute_id

where curdate() - interval 30 day > last_presentation
),
alle as (
select * from q1
union
select * from q2
union
select * from q3
)
select alle.* from alle
inner join wordlist_known_word wkw
on alle.word_id = wkw.word_id
where wkw.wordlist_id in (32)

order by rand()

-- limit 1
