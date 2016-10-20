use deutsch;

drop table if exists dative_verbs;

create table dative_verbs (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view dative_verbs_v as
select
		mashup.*
from
		mashup
inner join dative_verbs on mashup.word_id = dative_verbs.word_id
;
