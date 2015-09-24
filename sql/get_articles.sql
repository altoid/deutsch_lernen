-- for quizzes.  if the selected word is a noun, get the article

select * from
(
	select
		pos.name,
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
	inner join pos on w.pos_id = pos.id
	inner join word_attribute wa on w.id = wa.word_id
	      and wa.attribute_id = qstruct.attribute_id
	inner join quiz_score qscore on
	     w.id = qscore.word_id
	     and qstruct.quiz_id = qscore.quiz_id
	     and qstruct.attribute_id = qscore.attribute_id
	where
	 	q.quizkey = 'definitions' and
		presentation_count < 5

	order by
	      presentation_count,
	      (correct_count / presentation_count)

--	limit 1
;
