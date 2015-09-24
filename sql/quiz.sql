-- need quiz_id, word_id, attribute_id from other tables.  these are the PK of quiz_score.


	-- never tested
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       component
from
	(
	select
		w.word,
		wa.value, 
		q.id quiz_id,
		w.id word_id,
		wa.attribute_id,
		qscore.presentation_count,
		qscore.correct_count,
		'never_tested' component
	from quiz q
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	left join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = 'third_person_past' and
		qscore.word_id is null
	order by rand()
	limit 1
	) never_tested

union

-- crappy score (for words presented >= 5 times)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       component

from
	(	
	select
		w.word,
		wa.value,
		q.id quiz_id,
		w.id word_id,
		wa.attribute_id,
		qscore.presentation_count,
		qscore.correct_count,
		'crappy_score' component
	from quiz q
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = 'third_person_past' and
		presentation_count >= 5 and
		(correct_count / presentation_count) < 0.95
	order by
	      presentation_count,
	      (correct_count / presentation_count)
	limit 1
	) crappy_score

union

-- too few attempts (< 5)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       component

from
	(	
	select
		w.word,
		wa.value,
		q.id quiz_id,
		w.id word_id,
		wa.attribute_id,
		qscore.presentation_count,
		qscore.correct_count,
		'too_few_attempts' component
	from quiz q
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = 'third_person_past' and
		presentation_count < 5
	order by
	      presentation_count,
	      (correct_count / presentation_count)
	limit 1
	) too_few_attempts

union

-- too much time since last trial (30 days)
select 
       word, value, quiz_id, word_id, attribute_id,
       ifnull(presentation_count, 0) presentation_count,
       ifnull(correct_count, 0) correct_count,
       component

from
	(
	select
		w.word,
		wa.value,
		q.id quiz_id,
		w.id word_id,
		wa.attribute_id,
		qscore.presentation_count,
		qscore.correct_count,
		'been_too_long' component
	from quiz q
	inner join quiz_structure qstruct on q.id = qstruct.quiz_id
	inner join word w on qstruct.pos_id = w.pos_id
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = 'third_person_past' and
		CURDATE() - INTERVAL 30 DAY > last_presentation
	order by
	      last_presentation
	limit 1
	) been_too_long

order by rand()
 limit 1
;


/*

+---------+--------+--------------+-----+--------+---------------+
| quiz_id | pos_id | attribute_id | id  | pos_id | word          |
+---------+--------+--------------+-----+--------+---------------+
|       1 |      1 |            1 | 112 |      1 | abenteuer     |
|       1 |      1 |            1 |  84 |      1 | absicht       |
|       1 |      1 |            1 |  43 |      1 | apfel         |
|       1 |      1 |            1 | 132 |      1 | auge          |
|       1 |      1 |            1 | 151 |      1 | auswahl       |
|       1 |      1 |            1 |  34 |      1 | bad           |
|       1 |      1 |            1 |  87 |      1 | beleidigung   |
|       1 |      1 |            1 |  32 |      1 | beruf         |
|       1 |      1 |            1 | 123 |      1 | bett          |



mysql> select * from quiz_score;
+---------+---------+--------------+--------------------+---------------+---------------------+
| quiz_id | word_id | attribute_id | presentation_count | correct_count | last_presentation   |
+---------+---------+--------------+--------------------+---------------+---------------------+
|       1 |      15 |            1 |                  2 |             2 | 2013-04-18 12:06:44 |
|       1 |      16 |            1 |                  3 |             3 | 2013-04-19 14:11:41 |
|       1 |      17 |            1 |                  3 |             2 | 2013-04-16 16:24:05 |
|       1 |      18 |            1 |                  2 |             1 | 2013-04-19 10:30:13 |
|       1 |      19 |            1 |                  2 |             2 | 2013-04-19 10:27:20 |
|       1 |      20 |            1 |                  1 |             1 | 2013-04-16 14:56:34 |
|       1 |      21 |            1 |                  2 |             0 | 2013-04-19 14:18:58 |
|       1 |      22 |            1 |                  4 |             4 | 2013-04-19 14:17:43 |

*/


