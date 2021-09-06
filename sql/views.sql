use deutsch;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `acc_dat_preposition_v` AS select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`pos_id` AS `pos_id`,`mashup_v`.`pos_name` AS `pos_name`,`mashup_v`.`attribute_id` AS `attribute_id`,`mashup_v`.`attrkey` AS `attrkey`,`mashup_v`.`sort_order` AS `sort_order`,`mashup_v`.`attrvalue` AS `attrvalue` from (`mashup_v` join `acc_dat_preposition` on((`mashup_v`.`word_id` = `acc_dat_preposition`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `accusative_preposition_v` AS select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`pos_id` AS `pos_id`,`mashup_v`.`pos_name` AS `pos_name`,`mashup_v`.`attribute_id` AS `attribute_id`,`mashup_v`.`attrkey` AS `attrkey`,`mashup_v`.`sort_order` AS `sort_order`,`mashup_v`.`attrvalue` AS `attrvalue` from (`mashup_v` join `accusative_preposition` on((`mashup_v`.`word_id` = `accusative_preposition`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `dative_preposition_v` AS select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`pos_id` AS `pos_id`,`mashup_v`.`pos_name` AS `pos_name`,`mashup_v`.`attribute_id` AS `attribute_id`,`mashup_v`.`attrkey` AS `attrkey`,`mashup_v`.`sort_order` AS `sort_order`,`mashup_v`.`attrvalue` AS `attrvalue` from (`mashup_v` join `dative_preposition` on((`mashup_v`.`word_id` = `dative_preposition`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `genitive_preposition_v` AS select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`pos_id` AS `pos_id`,`mashup_v`.`pos_name` AS `pos_name`,`mashup_v`.`attribute_id` AS `attribute_id`,`mashup_v`.`attrkey` AS `attrkey`,`mashup_v`.`sort_order` AS `sort_order`,`mashup_v`.`attrvalue` AS `attrvalue` from (`mashup_v` join `genitive_preposition` on((`mashup_v`.`word_id` = `genitive_preposition`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `lookup_v` AS select `w`.`word` AS `word`,`l`.`count` AS `count`,`l`.`updated` AS `updated` from (`word` `w` join `lookup` `l` on((`w`.`id` = `l`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `mashup_v` AS select `w`.`id` AS `word_id`,`w`.`word` AS `word`,`w`.`added` AS `added`,`pos`.`id` AS `pos_id`,`pos`.`name` AS `pos_name`,`a`.`id` AS `attribute_id`,`a`.`attrkey` AS `attrkey`,`pf`.`sort_order` AS `sort_order`,`wa`.`value` AS `attrvalue` from (((((`pos` join `pos_form` `pf` on((`pos`.`id` = `pf`.`pos_id`))) join `attribute` `a` on((`a`.`id` = `pf`.`attribute_id`))) left join `word` `w` on((`w`.`pos_id` = `pos`.`id`))) left join `words_x_attributes_v` `v` on(((`v`.`pos_id` = `pos`.`id`) and (`v`.`attribute_id` = `a`.`id`) and (`v`.`word_id` = `w`.`id`)))) left join `word_attribute` `wa` on(((`wa`.`attribute_id` = `v`.`attribute_id`) and (`wa`.`word_id` = `v`.`word_id`))))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `preposition_case_v` AS select `dative_preposition_v`.`word_id` AS `word_id`,`dative_preposition_v`.`word` AS `word`,`dative_preposition_v`.`pos_id` AS `pos_id`,`dative_preposition_v`.`pos_name` AS `pos_name`,`dative_preposition_v`.`attribute_id` AS `attribute_id`,`dative_preposition_v`.`attrkey` AS `attrkey`,`dative_preposition_v`.`sort_order` AS `sort_order`,`dative_preposition_v`.`attrvalue` AS `attrvalue`,'dative' AS `case` from `dative_preposition_v` union select `accusative_preposition_v`.`word_id` AS `word_id`,`accusative_preposition_v`.`word` AS `word`,`accusative_preposition_v`.`pos_id` AS `pos_id`,`accusative_preposition_v`.`pos_name` AS `pos_name`,`accusative_preposition_v`.`attribute_id` AS `attribute_id`,`accusative_preposition_v`.`attrkey` AS `attrkey`,`accusative_preposition_v`.`sort_order` AS `sort_order`,`accusative_preposition_v`.`attrvalue` AS `attrvalue`,'accusative' AS `case` from `accusative_preposition_v` union select `genitive_preposition_v`.`word_id` AS `word_id`,`genitive_preposition_v`.`word` AS `word`,`genitive_preposition_v`.`pos_id` AS `pos_id`,`genitive_preposition_v`.`pos_name` AS `pos_name`,`genitive_preposition_v`.`attribute_id` AS `attribute_id`,`genitive_preposition_v`.`attrkey` AS `attrkey`,`genitive_preposition_v`.`sort_order` AS `sort_order`,`genitive_preposition_v`.`attrvalue` AS `attrvalue`,'genitive' AS `case` from `genitive_preposition_v` union select `acc_dat_preposition_v`.`word_id` AS `word_id`,`acc_dat_preposition_v`.`word` AS `word`,`acc_dat_preposition_v`.`pos_id` AS `pos_id`,`acc_dat_preposition_v`.`pos_name` AS `pos_name`,`acc_dat_preposition_v`.`attribute_id` AS `attribute_id`,`acc_dat_preposition_v`.`attrkey` AS `attrkey`,`acc_dat_preposition_v`.`sort_order` AS `sort_order`,`acc_dat_preposition_v`.`attrvalue` AS `attrvalue`,'accusative/dative' AS `case` from `acc_dat_preposition_v`
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `verb_tenses_v` AS select `def`.`word_id` AS `word_id`,`def`.`word` AS `infinitive`,`fps`.`attrvalue` AS `first_person_singular`,`sps`.`attrvalue` AS `second_person_singular`,`tps`.`attrvalue` AS `third_person_singular`,`tpt`.`attrvalue` AS `third_person_past`,`pp`.`attrvalue` AS `past_participle`,`def`.`attrvalue` AS `definition` from ((((((select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'definition'))) `def` left join (select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'first_person_singular'))) `fps` on((`fps`.`word_id` = `def`.`word_id`))) left join (select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'second_person_singular'))) `sps` on((`sps`.`word_id` = `def`.`word_id`))) left join (select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'third_person_singular'))) `tps` on((`tps`.`word_id` = `def`.`word_id`))) left join (select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'third_person_past'))) `tpt` on((`tpt`.`word_id` = `def`.`word_id`))) left join (select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`attrvalue` AS `attrvalue` from `mashup_v` where ((`mashup_v`.`pos_name` = 'verb') and (`mashup_v`.`attrkey` = 'past_participle'))) `pp` on((`pp`.`word_id` = `def`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `weak_noun_v` AS select `mashup_v`.`word_id` AS `word_id`,`mashup_v`.`word` AS `word`,`mashup_v`.`pos_id` AS `pos_id`,`mashup_v`.`pos_name` AS `pos_name`,`mashup_v`.`attribute_id` AS `attribute_id`,`mashup_v`.`attrkey` AS `attrkey`,`mashup_v`.`sort_order` AS `sort_order`,`mashup_v`.`attrvalue` AS `attrvalue` from (`mashup_v` join `weak_noun` on((`mashup_v`.`word_id` = `weak_noun`.`word_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `words_x_attributes_v` AS select `pf`.`pos_id` AS `pos_id`,`pf`.`attribute_id` AS `attribute_id`,`w`.`id` AS `word_id` from (`pos_form` `pf` join `word` `w` on((`pf`.`pos_id` = `w`.`pos_id`)))
;

CREATE OR REPLACE ALGORITHM=UNDEFINED DEFINER=`german`@`localhost` SQL SECURITY DEFINER VIEW `verb_prep_v` AS select `p`.`verb_case` AS `verb_case`,`wv`.`word` AS `verb`,`wp`.`word` AS `prep` from ((`verb_prep` `p` join `word` `wv` on((`wv`.`id` = `p`.`verb_id`))) join `word` `wp` on((`wp`.`id` = `p`.`prep_id`)))
;
