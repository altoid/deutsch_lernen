create or replace view mashup as
select
		w.id word_id,
		w.word,
		p.id pos_id,
		p.name pos_name,
		a.id attribute_id,
		a.attrkey,
		pf.sort_order sort_order,
		wa.value attrvalue
from
		word w
inner join pos p on w.pos_id = p.id
inner join word_attribute wa on wa.word_id = w.id
inner join attribute a on wa.attribute_id = a.id
inner join pos_form pf on pf.pos_id = p.id and pf.attribute_id = a.id
;
