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
where ww.wordlist_id = 95
order by ww.word
;
