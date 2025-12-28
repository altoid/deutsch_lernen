use deutsch;

-- this will select all the verbs that do NOT have a separable prefix

with parts as
(
select
    m1.word,
    case
        when regexp_like(m1.word, 'en$') = 1 then substring(m1.word, 1, char_length(m1.word) - 2)
        else substring(m1.word, 1, char_length(m1.word) - 1)
    end as stem,
    m1.attrvalue sps, m2.attrvalue tps, m3.attrvalue tpp,
    m1.word_id

from mashup_v m1
inner join mashup_v m2 on m1.word_id = m2.word_id
inner join mashup_v m3 on m2.word_id = m3.word_id

where m1.attrkey = 'second_person_singular'
and m2.attrkey = 'third_person_singular'
and m3.attrkey = 'third_person_past'

-- eliminate verbs that have a separable prefix.
and m1.attrvalue regexp '\\.*[[:blank:]]\\.*' = 0
),
identify_irregular as
(
select
    word_id,
    word,
    stem,
    sps,
    tps,
    tpp,
    case
        when substring(stem, 1, least(char_length(stem), char_length(sps))) <> substring(sps, 1, least(char_length(stem), char_length(sps))) then 1
        when substring(stem, 1, least(char_length(stem), char_length(tps))) <> substring(tps, 1, least(char_length(stem), char_length(tps))) then 1
        when substring(stem, 1, least(char_length(stem), char_length(tpp))) <> substring(tpp, 1, least(char_length(stem), char_length(tpp))) then 1
        else 0
    end irregular

from parts
where sps is not null
and tps is not null
and tpp is not null
)
select word_id
from identify_irregular
where irregular = 1
;
