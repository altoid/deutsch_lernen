CREATE or replace VIEW `quiz_v` AS
select quiz.`name` AS quizname,
quiz.quizkey,
quiz.id AS quiz_id,
qscore.attribute_id,
qscore.presentation_count,
qscore.correct_count,
qscore.last_presentation,
word.id AS word_id,
word.word,
word.added,
attribute.attrkey
from quiz
inner join quiz_structure qstruct on quiz.id = qstruct.quiz_id
inner join quiz_score qscore on qscore.quiz_id = quiz.id and qscore.attribute_id = qstruct.attribute_id
inner join attribute on attribute.id = qscore.attribute_id
inner join word on word.id = qscore.word_id
;

