-- select q.*, qs.*, qc.*

/*
with presentations as
(
select qs.*
from quiz_score qs
inner join quiz q
on q.id = qs.quiz_id
where q.quizkey = 'definitions'
and qs.attribute_id = 5
-- ),
-- selected_words as (
-- select id word_id from word where id > 5099
)
-- select * from selected_words s
-- left join presentations p on s.word_id = p.word_id

select * from presentations
;
*/

/*
quizzes test knowledge of the values of word attributes.
this view records the result of every word attribute tested by every quiz.
*/
/*
create view quiz_v
as
select
	quiz.`name` quizname, quiz.quizkey, quiz.id quiz_id,
	qscore.attribute_id, qscore.presentation_count, qscore.correct_count, qscore.last_presentation,
	word.id word_id, word.pos_id, word.word, word.added,
	attribute.attrkey,
	pos.`name` pos_name
from quiz
inner join quiz_structure qstruct on quiz.id = qstruct.quiz_id
inner join quiz_score qscore on qscore.quiz_id = quiz.id and qscore.attribute_id = qstruct.attribute_id
inner join word on word.id = qscore.word_id and word.pos_id = qstruct.pos_id
inner join attribute on attribute.id = qscore.attribute_id
inner join pos on pos.id = qstruct.pos_id
;

*/


/****** words that haven't been tested **********/

with presentations as (
select * from quiz_v
where quizkey = 'definitions'
and attrkey in ('definition')
),
selected_words as (
select id word_id from word
where id > 5099
)

-- word has been presented 5 or fewer times (or not at all)

select sw.*,
p.quizname, p.quizkey, p.quiz_id, p.attribute_id, p.last_presentation, p.word, p.added, p.attrkey,
ifnull(p.presentation_count, 0) presentation_count,
ifnull(p.correct_count, 0) correct_count
from selected_words sw
left join presentations p on sw.word_id = p.word_id
where ifnull(presentation_count, 0) <= 5

union

-- crappy score (<= 80% in 10 or more presentations

select sw.*,
p.quizname, p.quizkey, p.quiz_id, p.attribute_id, p.last_presentation, p.word, p.added, p.attrkey,
presentation_count,
correct_count
from selected_words sw
inner join presentations p on sw.word_id = p.word_id
where presentation_count >= 10
and correct_count / presentation_count <= 0.80

union

-- word hasn't been quizzed in more than 30 days

select sw.*,
p.quizname, p.quizkey, p.quiz_id, p.attribute_id, p.last_presentation, p.word, p.added, p.attrkey,
presentation_count,
correct_count
from selected_words sw
inner join presentations p on sw.word_id = p.word_id
where curdate() - interval 30 day > last_presentation

;
