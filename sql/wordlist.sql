select distinct
ww.wordlist_id,
ww.word list_word,
ww.added,
m.attrvalue definition,
ifnull(m2.attrvalue, '   ') article,
m.word dict_word
from wordlist_word ww
left join mashup m
on ww.word = m.word
and m.attrkey = 'definition'
left join mashup m2
on ww.word = m2.word
and m2.attrkey = 'article'
where ww.wordlist_id = 41
order by ww.word
;

select
ww.wordlist_id,
m.word,
ww.added,
m.attrvalue definition,
ifnull(m2.attrvalue, '   ') article
from wordlist_known_word ww
left join mashup m
on ww.word_id = m.word_id
and m.attrkey = 'definition'
left join mashup m2
on ww.word_id = m2.word_id
and m2.attrkey = 'article'
where ww.wordlist_id = 41
order by m.word
;

select
ww.wordlist_id,
ww.word list_word,
ww.added,
null definition,
'   ' article
from wordlist_unknown_word ww
left join mashup m
on ww.word = m.word
and m.attrkey = 'definition'
left join mashup m2
on ww.word = m2.word
and m2.attrkey = 'article'
where ww.wordlist_id = 41
order by ww.word
;
