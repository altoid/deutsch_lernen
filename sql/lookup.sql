select
    pos_name,
    word,
    word_id,
	concat(attrkey, ':') attrkey,
    attrvalue,
    pf.sort_order
from
    mashup
inner join pos_form pf on pf.attribute_id = mashup.attribute_id and pf.pos_id = mashup.pos_id
where
		word_id in
(
select
    word_id
from
    mashup
where
	word like '%geriet%' or attrvalue like '%geriet%'
)
order by word, sort_order
;

		
