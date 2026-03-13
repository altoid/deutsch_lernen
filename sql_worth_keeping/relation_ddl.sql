use deutsch;

drop table if exists word_id_relation;
drop table if exists relation;

create table relation
(
    id int not null auto_increment primary key,
    added timestamp not null default current_timestamp,
    notes text,
    description varchar(512)
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_german2_ci
;

create table word_id_relation
(
    word_id int not null,
    relation_id int not null,
    added timestamp not null default current_timestamp,
    unique key pair (word_id, relation_id),
    foreign key (word_id) references word(id) on delete cascade,
    foreign key (relation_id) references relation(id) on delete cascade
) DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_german2_ci
;
