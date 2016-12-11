use deutsch;

drop table if exists dative_preposition;

create table dative_preposition (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view dative_preposition_v as
select
		mashup.*
from
		mashup
inner join dative_preposition on mashup.word_id = dative_preposition.word_id
;

-- -------------------------------------

drop table if exists accusative_preposition;

create table accusative_preposition (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view accusative_preposition_v as
select
		mashup.*
from
		mashup
inner join accusative_preposition on mashup.word_id = accusative_preposition.word_id
;

-- -------------------------------------

drop table if exists genitive_preposition;

create table genitive_preposition (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view genitive_preposition_v as
select
		mashup.*
from
		mashup
inner join genitive_preposition on mashup.word_id = genitive_preposition.word_id
;

-- -------------------------------------

drop table if exists acc_dat_preposition;

create table acc_dat_preposition (
	   word_id			  int not null primary key,
	   foreign key (word_id) references word(id) on delete cascade
) engine=innodb
;

create or replace view acc_dat_preposition_v as
select
		mashup.*
from
		mashup
inner join acc_dat_preposition on mashup.word_id = acc_dat_preposition.word_id
;
