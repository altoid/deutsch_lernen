
create table wordlist_known_word (
  `wordlist_id` int NOT NULL,
  word_id int not null,
  `added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`wordlist_id`,`word_id`),
  CONSTRAINT `wordlist_known_word_ibfk_1` FOREIGN KEY (`wordlist_id`) REFERENCES `wordlist` (`id`) ON DELETE CASCADE,
  CONSTRAINT `wordlist_known_word_ibfk_2` FOREIGN KEY (`word_id`) REFERENCES `word` (`id`) ON DELETE CASCADE
) engine=innodb default charset=utf8 collate=utf8_swedish_ci
;

create table wordlist_unknown_word (

  `wordlist_id` int NOT NULL,
  `word` varchar(64) CHARACTER SET utf8 COLLATE utf8_swedish_ci NOT NULL,
  `added` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`wordlist_id`,`word`),
  CONSTRAINT `wordlist_unknown_word_ibfk_1` FOREIGN KEY (`wordlist_id`) REFERENCES `wordlist` (`id`) ON DELETE CASCADE

) engine=innodb default charset=utf8 collate=utf8_swedish_ci
;
