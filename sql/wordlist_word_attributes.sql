-- given a word_id and a wordlist_id, give me the word ids for all the parts of speech for this word in the wordlist.
--
-- for example, if the word 'blarg' is a noun, a verb, and an
-- adjective, give me the word ids for all of these, even if the word
-- list only contains the noun.

-- 548 is the id for the noun 'der Rasen'
select
    word_id, word, pos_id, pos_name, attribute_id, attrkey, attrvalue, sort_order
from mashup
where word_id in
(
	select id from word
	where word in (
	      select word from word where word = 'rasen'
	)
)
;

select
	x.word,
	a.word,	a.word_id, a.pos_id, a.pos_name, a.attribute_id, a.attrkey, a.attrvalue, a.sort_order
from
(select 'rasen' word from dual) x
left join
(
	select
	    word_id, word, pos_id, pos_name, attribute_id, attrkey, attrvalue, sort_order
	from mashup
) a
on a.word = x.word
;
