use deutsch;

create or replace view verb_prefix_v as
select
    word, word_id,
    extracted_prefix,
    prefix, prefix_word_id,
    grundverb, grundverb_word_id,
    pos_name, pos_id
from separable_prefix_v

union

select
    word, word_id,
    extracted_prefix,
    prefix, prefix_word_id,
    grundverb, grundverb_word_id,
    pos_name, pos_id
from inseparable_prefix_v
;
