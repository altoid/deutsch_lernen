use deutsch;

-- gimme all the separable prefixes
with extracted_prefix as
(
select
SUBSTRING_INDEX(attrvalue, ' ', -1) prefix, word_id, word,
    substring(word, char_length(attrvalue) - instr(attrvalue, ' ') + 1) root
from mashup_v
where attrkey = 'second_person_singular'
and attrvalue like '% %'
)
select distinct
    extracted_prefix.word_id,
    extracted_prefix.word,
    m1.word_id root_word_id,
    m1.word root,
    m2.word_id prefix_word_id,
    m2.word prefix
from extracted_prefix

inner join mashup_v m1 on extracted_prefix.root = m1.word
inner join mashup_v m2 on extracted_prefix.prefix = m2.word

where m1.pos_name = 'verb'
and m2.pos_name = 'separable prefix'

order by prefix, root
;

-- for every verb, gimme:
--
--     its word id
--     the word id of its separable prefix if it has one
--     the word_id of its root if it has a separable prefix
--
--     entgehen     ent      gehen
--     gehen        NULL     NULL
--     hinausgehen  hinaus   gehen       -- prefix is hinaus, not hin, and root is gehen, not ausgehen
--     ausgehen     aus      gehen
--     abgehen      ab       gehen
--
--     we'll rely on second person singular conjugations to provide the separable prefixes.
