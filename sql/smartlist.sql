-- give me verbs with 'fall' in them

select
	word,
	attrvalue
from mashup
where pos_name = 'verb'
and word like '%fall%'
and attrkey in ('definition')
;

