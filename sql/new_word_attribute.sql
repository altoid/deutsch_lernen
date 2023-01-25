use deutsch;

create table if not exists word_attribute_dummy
(
	attribute_id int not null,
	word_id int not null,
	value_id int not null auto_increment,
	attrvalue varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
	key (value_id),
	unique key meh (attribute_id, word_id, value_id),
	foreign key (attribute_id) references attribute(id) on delete cascade,
	foreign key (word_id) references word(id) on delete cascade
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
;

create table if not exists attrvalue
(
	id int not null auto_increment primary key,
	attrvalue varchar(1024) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
;

create table if not exists new_word_attribute
(
	attribute_id int not null,
	word_id int not null,
	attrvalue_id int not null,
	unique key (attribute_id, word_id, attrvalue_id),
	foreign key (attribute_id) references attribute(id) on delete cascade,
	foreign key (word_id) references word(id) on delete cascade,
	foreign key (attrvalue_id) references attrvalue(id) on delete cascade
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
;
	
	
