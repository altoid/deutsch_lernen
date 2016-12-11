use deutsch;

drop table if exists dative_verb;

create table dative_verb (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view dative_verb_v as
select
		mashup.*
from
		mashup
inner join dative_verb on mashup.word_id = dative_verb.word_id
;
