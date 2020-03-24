-- treat the list of irregular verbs as a view.  that way we can compare with the word table
-- to see what is missing.

use deutsch;

/*
drop table if exists irregular_verb_list;

create table irregular_verb_list
(
		word varchar(64) collate utf8_unicode_ci not null primary key
) engine=innodb default charset=utf8 collate utf8_swedish_ci
;
*/

-- to find irregular verbs here that aren't in the word table:
-- select l.word, w.word from irregular_verb_list l left join word w on l.word = w.word where w.word is null;

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
