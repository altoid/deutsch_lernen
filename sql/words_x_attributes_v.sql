select
	pf.pos_id AS pos_id,
	pf.attribute_id AS attribute_id,
	w.id AS word_id from (pos_form pf join word w on((pf.pos_id = w.pos_id)))
;

