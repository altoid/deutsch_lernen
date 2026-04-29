use deutsch;

-- gimme all the separable prefixes
with extracted_prefix as
(
select
SUBSTRING_INDEX(attrvalue, ' ', -1) prefix, word_id, word,
    substring(word, char_length(attrvalue) - instr(attrvalue, ' ') + 1) root
from mashup_v
where attrkey = 'third_person_singular'
and attrvalue like '% %'
),
separable_prefix as (
-- this will give the word_ids for the verb, the separable prefix, and the root, subject to the following conditions:
--
-- 1.  the third person singular for the verb is present
-- 2.  the SPS shows that there is a separable prefix
-- 3.  the prefix exists in the database
-- 4.  the root exists in the database
--
select distinct
extracted_prefix.word_id, m1.word_id prefix_word_id, m2.word_id root_word_id
from extracted_prefix

inner join mashup_v m1
on m1.word = extracted_prefix.prefix

inner join mashup_v m2
on m2.word = extracted_prefix.root

where m1.pos_name = 'separable prefix'
and m2.pos_name = 'verb'
)
select * from separable_prefix
;
