-- give me verbs with 'nehm' in them

insert ignore into wordlist_word (wordlist_id, word)
select distinct
	wl.id, w.word
from mashup w, wordlist wl
where pos_name = 'verb'
and w.word like '%nehm%'
and wl.name = 'verbs like \'nehm\''
;

