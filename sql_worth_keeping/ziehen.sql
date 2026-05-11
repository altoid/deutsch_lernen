use deutsch;

with grundverb as
(
    select distinct word_id
    from mashup_v
    where pos_name = 'verb'
    and word in ('ziehen', 'erziehen')
)
select distinct separable_prefix_v.word_id
from separable_prefix_v
inner join grundverb
where grundverb_word_id = grundverb.word_id

union

select distinct inseparable_prefix_v.word_id
from inseparable_prefix_v
inner join grundverb
where grundverb_word_id = grundverb.word_id

union

select distinct word_id
from grundverb

;
