use deutsch;

\W

create table if not exists lookup
(
		word_id int not null primary key,
		count int not null default 1,
		foreign key (word_id) references word(id) on delete cascade
) engine=innodb;
