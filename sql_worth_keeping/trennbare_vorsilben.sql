use deutsch;

-- gimme all the separable prefixes
create or replace view separable_prefix_v as
with extracted_prefix as
(
select
SUBSTRING_INDEX(attrvalue, ' ', -1) prefix, word_id, word,
    substring(word, char_length(attrvalue) - instr(attrvalue, ' ') + 1) grundverb
from mashup_v
where attrkey = 'third_person_singular'
and attrvalue like '% %'
),
separable_prefix as (
-- this will give the word_ids for the verb, the separable prefix, and the grundverb, subject to the following conditions:
--
-- 1.  the third person singular for the verb is present
-- 2.  the SPS shows that there is a separable prefix
-- 3.  the prefix exists in the database
-- 4.  the grundverb exists in the database
--
select distinct
extracted_prefix.word_id, extracted_prefix.word,
m1.word_id prefix_word_id, m1.word prefix,
extracted_prefix.prefix extracted_prefix,
m2.word_id grundverb_word_id, m2.word grundverb
from extracted_prefix

inner join mashup_v m2
on m2.word = extracted_prefix.grundverb and m2.pos_name = 'verb'

left join mashup_v m1
on m1.word = extracted_prefix.prefix and m1.pos_name = 'separable prefix'
),
pos_info as (
    select id pos_id, name pos_name
    from pos
    where name = 'Separable Prefix'
)
select
    word, word_id,                -- verb with prefix and its id.
    extracted_prefix,             -- prefix as extracted from the word.  this is derived.  with math.
    prefix, prefix_word_id,       -- prefix and its id.  might be null; prefix doesn't have to be in the dictionary.
    grundverb, grundverb_word_id, -- grundverb and its id.
    pos_name, pos_id

from separable_prefix, pos_info
;
