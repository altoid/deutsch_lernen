use deutsch;

-- to identify inseparable prefixes, do an auto-join of the word table to itself, on all the verbs.
-- the join condition is that len(A) > len(B) and B is a suffix of A.

create or replace view inseparable_prefix_v as
with inseparable_prefix as
(
    select distinct
        w1.word_id, w1.word,
        w2.word_id grundverb_word_id, w2.word grundverb,
        w3.word_id prefix_word_id, w3.word prefix

    from mashup_v w1
    inner join mashup_v w2
    on w1.pos_id = 2 and w2.pos_id = 2
    and w1.attrkey = 'third_person_singular' and w2.attrkey = 'third_person_singular'
    and w1.attrvalue not like '% %'  -- w1 can't have separable prefix.
    and char_length(w1.word) > char_length(w2.word)
    and substring(w1.word, -char_length(w2.word)) = w2.word
    
    inner join mashup_v w3
    on substring(w1.word, 1, char_length(w1.word) - char_length(w2.word)) = w3.word
    and w3.pos_id = 10  -- inseparable prefix
),
pos_info as (
    select id pos_id, name pos_name
    from pos
    where name = 'Inseparable Prefix'
)
select
    word, word_id,
    NULL as extracted_prefix,
    prefix, prefix_word_id,
    grundverb, grundverb_word_id,
    pos_name, pos_id

from inseparable_prefix, pos_info
;