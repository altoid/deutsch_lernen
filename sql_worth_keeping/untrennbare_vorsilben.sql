use deutsch;

-- to identify inseparable prefixes, do an auto-join of the word table to itself, on all the verbs.
-- the join condition is that len(A) > len(B) and B is a suffix of A.

select distinct
    w1.word, w1.word_id, w2.word, w2.word_id,
    substring(w1.word, 1, char_length(w1.word) - char_length(w2.word)) prefix,
    1
from mashup_v w1, mashup_v w2
where w1.pos_id = 2 and w2.pos_id = 2
and w1.attrkey = 'second_person_singular' and w2.attrkey = 'second_person_singular'
and w1.attrvalue not like '% %'  -- w1 can't have separable prefix.
and char_length(w1.word) > char_length(w2.word)
and substring(w1.word, -char_length(w2.word)) = w2.word
order by prefix
;