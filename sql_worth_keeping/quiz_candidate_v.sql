use deutsch;

-- for each quiz, give the defined attributes and the attribute values for candidate words.

create or replace view quiz_candidate_v as
select
    q.quiz_key,
    q.id quiz_id,
    m.word_id,
    m.word,
    m.pos_id,
    m.pos_name,
    m.attribute_id,
    m.attrkey,
    m.sort_order,
    m.attrvalue,
    qscore.last_presentation,
    ifnull(qscore.correct_count, 0) correct_count,
    ifnull(qscore.presentation_count, 0) presentation_count,
    ifnull(qscore.correct_count / qscore.presentation_count, 0.0) raw_score

from quiz q
inner join quiz_structure qs on qs.quiz_id = q.id
left join mashup_v m on qs.attribute_id = m.attribute_id
left join quiz_score_v qscore
    on qscore.quiz_id = qs.quiz_id
    and qscore.word_id = m.word_id
    and qscore.attribute_id = m.attribute_id
;
