# quiz works by testing for knowledge of 
# the attrkey values of chosen words.

# quiz - stores name and id of quiz along with a mnemonic.
#
# quiz_structure - (quiz_id, attribute_id)
# for each quiz, specify the part of speech and the attributes that 
# are tested.
#
# mysql> desc quiz_score;
# +--------------------+-----------+------+-----+-------------------+-----------------------------+
# | Field              | Type      | Null | Key | Default           | Extra                       |
# +--------------------+-----------+------+-----+-------------------+-----------------------------+
# | quiz_id            | int(11)   | NO   | PRI | NULL              |                             |
# | word_id            | int(11)   | NO   | PRI | NULL              |                             |
# | attribute_id       | int(11)   | NO   | PRI | NULL              |                             |
# | presentation_count | int(11)   | NO   |     | 0                 |                             |
# | correct_count      | int(11)   | NO   |     | 0                 |                             |
# | last_presentation  | timestamp | NO   |     | CURRENT_TIMESTAMP | on update CURRENT_TIMESTAMP |
# +--------------------+-----------+------+-----+-------------------+-----------------------------+
#
# scores for every quiz/word/attrkey, plus presentation time.
#
# how we select what to test:
#
# - crappiest score
# - too few attempts
# - been a long time
#
# for a score over 95%, don't retest.  unless it's been more than 30 days.

ATTRS_FOR_QUIZ = """
attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quiz_key = %s
)"""

TESTABLE_ATTRS_AND_VALUES = """
testable_attrs_and_values as (
select a.*, m.attrkey, m.word_id, m.word, m.attrvalue
from attrs_for_quiz a
inner join mashup_v m
on a.attribute_id = m.attribute_id
where attrvalue is not null
)"""

TESTABLE_ATTRS_AND_VALUES_WITH_WORDIDS_GIVEN = """
testable_attrs_and_values as (
select a.*, m.attrkey, m.word_id, m.word, m.attrvalue
from attrs_for_quiz a
inner join mashup_v m
on a.attribute_id = m.attribute_id
where attrvalue is not null                                                                                   
and m.word_id in (%(wordid_args)s)                                                                                   
)"""

PRESENTED_TOO_FEW_TIMES = """
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
)"""

CRAPPY_SCORE = """
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
)"""

BEEN_TOO_LONG = """
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
)"""


def build_quiz_query(word_ids=None):
    if word_ids:
        wordid_args = ['%s'] * len(word_ids)
        d = {
            'wordid_args': ', '.join(wordid_args)
        }

        subqueries = [
            ATTRS_FOR_QUIZ,
            TESTABLE_ATTRS_AND_VALUES_WITH_WORDIDS_GIVEN % d,
            PRESENTED_TOO_FEW_TIMES,
            CRAPPY_SCORE,
            BEEN_TOO_LONG
        ]
    else:
        subqueries = [
            ATTRS_FOR_QUIZ,
            TESTABLE_ATTRS_AND_VALUES,
            PRESENTED_TOO_FEW_TIMES,
            CRAPPY_SCORE,
            BEEN_TOO_LONG
        ]

    quiz_sql = """
with 
""" + ', '.join(subqueries) + """,
alle as (
select * from q1
union
select * from q2
union
select * from q3
)
select alle.* from alle

order by rand()

limit 1
"""

    return quiz_sql
