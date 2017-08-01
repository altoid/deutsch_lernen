use deutsch;

create or replace view
verb_prep_v
as
select
p.verb_case,
wv.word verb,
wp.word prep
from verb_prep p
inner join word wv on wv.id = p.verb_id
inner join word wp on wp.id = p.prep_id
;
