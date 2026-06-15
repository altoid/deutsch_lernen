use deutsch;

with candidate_word_id as
(
    select
        qc.quiz_id,
        qc.word_id,
        qc.word,
        qc.attribute_id,
        qc.attrvalue,
        qc.sort_order,
        ww.wordlist_id
        -- tag is not selected.  we want to filter with it, not see it.

    from quiz_candidate_v qc
    inner join wordlist_word ww
    on qc.word_id = ww.word_id

--    inner join tag
--    on ww.word_id = tag.word_id and ww.wordlist_id = tag.wordlist_id

    where quiz_key = 'present_indicative'
    and ww.wordlist_id = 12735
--    and tag in ('1025', '1145', 'testtag')

    -- for smart lists we have to give all the word ids, but there won't be any tags
),
incomplete_candidates as
(
    select distinct word_id
    from candidate_word_id
    where attrvalue is null
)
select distinct
    candidate.quiz_id,
    candidate.word_id,
    candidate.word,
    candidate.attribute_id,
    candidate.attrvalue,
    candidate.sort_order,
    candidate.wordlist_id,
    score.last_presentation,
    ifnull(score.correct_count, 0) correct_count,
    ifnull(score.presentation_count, 0) presentation_count,
    ifnull(score.correct_count / score.presentation_count, 0) raw_score

from candidate_word_id candidate
left join quiz_score_v score on score.quiz_id = candidate.quiz_id and score.word_id = candidate.word_id

where candidate.word_id not in (select word_id from incomplete_candidates)


order by word_id, sort_order


;
