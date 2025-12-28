use deutsch;

WITH without_prefix AS
(
SELECT
    m1.word,
    case
        when m1.attrvalue regexp '\\.*[[:blank:]]\\.*' = 1
            then substring_index(m1.attrvalue, ' ', -1)
        else null
    end prefix,

    case
        when m1.attrvalue regexp '\\.*[[:blank:]]\\.*' = 1
            then substring(m1.word, char_length(substring_index(m1.attrvalue, ' ', -1)) + 1)
        else m1.word
    end word_no_prefix,

    case
        when m1.attrvalue regexp '\\.*[[:blank:]]\\.*' = 1 then substring_index(m1.attrvalue, ' ', 1)
        else m1.attrvalue
    end as sps_no_prefix,

    case
        when m2.attrvalue regexp '\\.*[[:blank:]]\\.*' = 1 then substring_index(m2.attrvalue, ' ', 1)
        else m2.attrvalue
    end as tps_no_prefix,

    case
        when m3.attrvalue regexp '\\.*[[:blank:]]\\.*' = 1 then substring_index(m3.attrvalue, ' ', 1)
        else m3.attrvalue
    end as tpp_no_prefix,

    m1.word_id

from mashup_v m1
inner join mashup_v m2 on m1.word_id = m2.word_id
inner join mashup_v m3 on m2.word_id = m3.word_id

where m1.attrkey = 'second_person_singular'
and m2.attrkey = 'third_person_singular'
and m3.attrkey = 'third_person_past'

),
stem as (
    select
        ifnull(prefix, '') prefix,
        word_no_prefix as word,
        case
            when REGEXP_LIKE(word_no_prefix, 'en$') = 1 then substring(word_no_prefix, 1, char_length(word_no_prefix) - 2)
            else substring(word_no_prefix, 1, char_length(word_no_prefix) - 1)
        end as stem,
        sps_no_prefix as sps,
        tps_no_prefix as tps,
        tpp_no_prefix as tpp,
        word_id
    from without_prefix
),
identify_irregular as
(
SELECT
    word_id,
    word,
    stem,
    sps,
    tps,
    tpp,
    CASE
        WHEN substring(stem, 1, LEAST(char_length(stem), char_length(sps))) <> substring(sps, 1, LEAST(char_length(stem), char_length(sps))) THEN 1
        WHEN substring(stem, 1, LEAST(char_length(stem), char_length(tps))) <> substring(tps, 1, LEAST(char_length(stem), char_length(tps))) THEN 1
        WHEN substring(stem, 1, LEAST(char_length(stem), char_length(tpp))) <> substring(tpp, 1, LEAST(char_length(stem), char_length(tpp))) THEN 1
        ELSE 0
    END irregular

FROM stem
WHERE sps IS NOT NULL
AND tps IS NOT NULL
AND tpp IS NOT NULL
)
SELECT *
FROM identify_irregular

ORDER BY rand()
limit 33
;
