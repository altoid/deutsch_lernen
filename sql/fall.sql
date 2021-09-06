-- give me verbs with 'fall' in them

insert ignore into wordlist_word (wordlist_id, word)
select distinct
	wl.id, w.word
from mashup w, wordlist wl
where pos_name = 'verb'
and w.word like '%fall%'
and wl.name = 'verbs like \'fall\''
;

