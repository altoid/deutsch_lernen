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

next_item_query = """
-- need quiz_id, word_id, attribute_id from other tables.  these are the PK of quiz_score.


	-- never tested
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count
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
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
    %(filter)s
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	left join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = '%(quizkey)s' and
		qscore.word_id is null
        order by rand()
	limit 2
	) never_tested

union

-- crappy score (for words presented >= 5 times)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count
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
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
    %(filter)s
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = '%(quizkey)s' and
		presentation_count > 5 and
		(correct_count / presentation_count) <= 0.95
	order by
	      presentation_count,
	      (correct_count / presentation_count)
	limit 2
	) crappy_score

union

-- too few attempts (< 5)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count
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
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
    %(filter)s
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = '%(quizkey)s' and
		presentation_count <= 5
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
       ifnull(correct_count, 0) correct_count
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
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
    %(filter)s
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = '%(quizkey)s' and
		CURDATE() - INTERVAL 30 DAY > last_presentation
	order by
	      last_presentation
	limit 2
	) been_too_long

order by rand()
limit 1
"""


