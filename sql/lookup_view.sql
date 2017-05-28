use deutsch;

create or replace view lookup_v as
select
		w.word,
		l.count,
		l.updated
from
		word w
inner join lookup l
	  on w.id = l.word_id
;
