select
	t.name "part of speech",
	concat(ifnull(wa.value, '   '), ' ', t.word) word,
	t.value definition, 
	date(t.added) added
from
(
	select
		p.name, w.word, w.added, wa.*
	from
		word w
	inner join word_attribute wa on w.id = wa.word_id
	inner join attribute a on wa.attribute_id = a.id
	inner join pos p on p.id = w.pos_id
	where
		a.attrkey = 'definition'
) t
left join
word_attribute wa
on t.word_id = wa.word_id and wa.attribute_id = 1

where date_sub(now(), interval 1 day) <= t.added
order by t.added desc
-- limit 10
-- order by length(t.value) desc
;
