-- populate wordlist_known_word from wordlist_word. find words in wordlists that are more than 1 part of speech.

select a.*, wl.name
from
(
    select
    	wlw.wordlist_id,
    	w.word,
    	count(*)
    from wordlist_word wlw
    inner join word w on wlw.word = w.word
    group by wlw.wordlist_id, w.word
    having count(*) > 1
    ) a
inner join wordlist wl on wl.id = a.wordlist_id
order by wordlist_id, word
;

/*

insert into wordlist_known_word
select
    a.wordlist_id,
    w.id,
    wlw.added
from
(
    select
    	wlw.wordlist_id,
    	w.word
    from wordlist_word wlw
    inner join word w on wlw.word = w.word
    group by wlw.wordlist_id, w.word
    having count(*) = 1
) a
inner join word w on a.word = w.word
inner join wordlist_word wlw on wlw.wordlist_id = a.wordlist_id and wlw.word = a.word
;
*/

/*
-- give me all of the words in wordlists that don't appear in the dictionary.

insert into wordlist_unknown_word
select
	wlw.*
from wordlist_word wlw
left join word w on w.word = wlw.word
where w.word is null
;
*/
