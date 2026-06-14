create or replace view quiz_score_v as
select
    quiz_id, word_id, attribute_id,
    cast(sum(correct) as signed) correct_count, count(*) presentation_count, max(added) last_presentation
from quiz_score_event
group by quiz_id, attribute_id, word_id
;
