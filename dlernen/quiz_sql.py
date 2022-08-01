# quiz works by testing for knowledge of 
# the attribute values of chosen words.

# quiz - stores name and id of quiz along with a mnemonic.
#
# quiz_structure - (quiz_id, pos_id, attribute_id)
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
# quiz_attr_count
# NFI
#
# quiz_word_attr_count
# NFI
#
# how we select what to test:
#
# - crappiest score
# - never tested
# - too few attempts
# - been a long time
#
# for a score over 95%, don't retest.  unless it's been more than 30 days.

join_clauses = [
    "inner join quiz_structure qstruct on q.id = qstruct.quiz_id",
    "inner join word w on qstruct.pos_id = w.pos_id",
    "inner join word_attribute wa on w.id = wa.word_id and wa.attribute_id = qstruct.attribute_id",
    """left join quiz_score qscore on
             w.id = qscore.word_id
             and qstruct.quiz_id = qscore.quiz_id
             and qstruct.attribute_id = qscore.attribute_id"""
]

never_tested_filter = ["""qscore.word_id is null"""]
crappy_score_filter = [
    """presentation_count > 5""",
    """(correct_count / presentation_count) <= 0.80"""]

too_few_attempts_filter = [
    """presentation_count <= 5"""]

been_too_long_filter = ["""CURDATE() - INTERVAL 30 DAY > last_presentation"""]

next_item_query = """
-- need quiz_id, word_id, attribute_id from other tables.  these are the PK of quiz_score.


        -- never tested
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       'never_tested' method
from
        (
        select
                w.word,
                wa.value, 
                q.id quiz_id,
                w.id word_id,
                wa.attribute_id,
                qscore.presentation_count,
                qscore.correct_count
        from quiz q
        {join_clauses}
        where
                {never_tested_filter}
        order by rand()
        limit 2
        ) never_tested

union

-- crappy score (for words presented >= 10 times)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       'crappy_score' method
from
        (       
        select
                w.word,
                wa.value,
                q.id quiz_id,
                w.id word_id,
                wa.attribute_id,
                qscore.presentation_count,
                qscore.correct_count
        from quiz q
        {join_clauses}
        where
              {crappy_score_filter}
        order by
              presentation_count,
              (correct_count / presentation_count)
        limit 2
        ) crappy_score

union

-- too few attempts (<= 5)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       'too_few_attempts' method
from
        (       
        select
                w.word,
                wa.value,
                q.id quiz_id,
                w.id word_id,
                wa.attribute_id,
                qscore.presentation_count,
                qscore.correct_count
        from quiz q
        {join_clauses}
        where
              {too_few_attempts_filter}
        order by
              presentation_count,
              (correct_count / presentation_count)
        limit 2
        ) too_few_attempts

union

-- too much time since last trial (30 days)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       'been_too_long' method
from
        (
        select
                w.word,
                wa.value,
                q.id quiz_id,
                w.id word_id,
                wa.attribute_id,
                qscore.presentation_count,
                qscore.correct_count
        from quiz q
        {join_clauses}
        where
              {been_too_long_filter}
        order by
              last_presentation
        limit 2
        ) been_too_long

order by rand()
limit 1
"""


def build_quiz_query(quizkey, **kwargs):
    global never_tested_filter
    global crappy_score_filter
    global been_too_long_filter
    global too_few_attempts_filter

    join_clauses_arg = kwargs.get('join_clauses', [])
    where_clauses = kwargs.get('where_clauses', [])

    j_clauses = join_clauses + join_clauses_arg
    j_clauses = ' '.join(j_clauses)
    d1 = {
        'quizkey': quizkey,
    }

    qkey = "q.quizkey = '{quizkey}'".format(**d1)
    never_tested_filter += [qkey] + where_clauses
    crappy_score_filter += [qkey] + where_clauses
    too_few_attempts_filter += [qkey] + where_clauses
    been_too_long_filter += [qkey] + where_clauses

    d2 = {
        'join_clauses': j_clauses,
        'never_tested_filter': ' AND '.join(never_tested_filter),
        'crappy_score_filter': ' AND '.join(crappy_score_filter),
        'been_too_long_filter': ' AND '.join(been_too_long_filter),
        'too_few_attempts_filter': ' AND '.join(too_few_attempts_filter),
    }

    return next_item_query.format(**d2)
