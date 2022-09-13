show warnings;

drop table if exists quiz_structure;

CREATE TABLE `quiz_structure` (
  `quiz_id` int NOT NULL,
  `attribute_id` int NOT NULL,
  primary KEY (`quiz_id`,`attribute_id`),
  KEY `attribute_id` (`attribute_id`),
  CONSTRAINT `quiz_structure_ibfk_1` FOREIGN KEY (`quiz_id`) REFERENCES `quiz` (`id`) ON DELETE CASCADE,
  CONSTRAINT `quiz_structure_ibfk_2` FOREIGN KEY (`attribute_id`) REFERENCES `attribute` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
;

insert into quiz_structure (quiz_id, attribute_id)
values
(   1 ,           1),
(   2 ,           5),
(   3 ,           3),
(   4 ,           6),
(   4 ,           7),
(   4 ,           8),
(   4 ,           9),
(   4 ,          10),
(   4 ,          11),
(   5 ,          16),
(   6 ,          17)
;

