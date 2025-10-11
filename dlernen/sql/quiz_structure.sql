use deutsch;

select *
from quiz q
inner join quiz_structure qs
on q.id = qs.quiz_id
inner join attribute a
on qs.attribute_id = a.id
;
