use deutsch;

drop table if exists irregular_verb;

create table irregular_verb (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view irregular_verb_v as
select
		mashup.*
from
		mashup
inner join irregular_verb on mashup.word_id = irregular_verb.word_id
;
