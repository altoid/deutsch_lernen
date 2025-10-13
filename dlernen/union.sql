-- build a query out of the sqlcode of multiple (smart) wordlists

select distinct word_id
from mashup_v
where pos_name = 'verb'
and word like '%kommen'

union

select distinct word_id
from mashup_v
where word like '%irgend%'

union

select distinct word_id 
from mashup_v where word like '%iv' and pos_name = 'Noun'

union

select distinct word_id
from wordlist_known_word
where wordlist_id in (
1619,1620,1621,1622,1623,1624,1625,1626,1627,1628,1629,1618,1630)

union

select distinct word_id 
from wordlist_known_word 
where wordlist_id in (
1619,1620,1621,1622,1623,1624,1625,1626,1627,1628,1629,1618,1630)

order by word_id
;
