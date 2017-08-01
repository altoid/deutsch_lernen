use deutsch;

create table if not exists
verb_prep
(
		verb_case varchar(10) not null,
		verb_id int not null,
		prep_id int not null,
		primary key (verb_case, verb_id, prep_id),
		foreign key (verb_id) references word(id) on delete cascade,
		foreign key (prep_id) references word(id) on delete cascade
) engine=innodb
;
