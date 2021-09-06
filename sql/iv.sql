\W

use deutsch;

insert ignore into wordlist_word (wordlist_id, word)
select id wordlist_id, w word from
(
select 'aoeu' as w union
select 'fffaoeu' as w union
select 'aoeaeuieuiu' as w
) b
inner join (select id from wordlist wl where name = 'irregular verbs') x
;
