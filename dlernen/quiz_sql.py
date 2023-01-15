# quiz works by testing for knowledge of 
# the attribute values of chosen words.

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
# scores for every quiz/word/attribute, plus presentation time.
#
# how we select what to test:
#
# - crappiest score
# - too few attempts
# - been a long time
#
# for a score over 95%, don't retest.  unless it's been more than 30 days.

QUIZ_SQL = """
with attrs_for_quiz as (
select qs.quiz_id, qs.attribute_id
from quiz
inner join quiz_structure qs on quiz.id = qs.quiz_id
where quizkey = '{quizkey}'
),
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

-- word has been presented 5 or fewer times (or not at all)

select
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

union

-- crappy score (<= 80% in 10 or more presentations

select
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

union

-- word hasn't been quizzed in more than 30 days

select
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

order by rand()

-- limit 1
"""


def build_quiz_query(quizkey, word_ids):
    """
    word_ids should be a string that is a comma-separated list of word_ids
    """
    d = {
        "quizkey": quizkey,
        "word_ids": word_ids
    }

    return QUIZ_SQL.format(**d)
