use deutsch;

-- gimme all the separable prefixes
with prefixes as
(
select
SUBSTRING_INDEX(attrvalue, ' ', -1) prefix, word_id, word,
    substring(word, char_length(attrvalue) - instr(attrvalue, ' ') + 1) root
from mashup_v
where attrkey = 'second_person_singular'
and attrvalue like '% %'
)
select distinct prefixes.*, mashup_v.word_id root_word_id, mashup_v.word
from prefixes
inner join mashup_v on prefixes.root = mashup_v.word
where pos_name = 'verb'
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
