use deutsch;

create or replace view lookup_v as
select
		w.word,
		l.count
from
		word w
inner join lookup l
	  on w.id = l.word_id
;
