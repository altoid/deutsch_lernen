with m_and_n_nouns as
(
select word_id, attrvalue article
from mashup_v
where attrkey = 'article'
and attrvalue in ('der', 'das')
),
plurals as
(
select word_id, word, attrvalue plural
from mashup_v
where attrkey = 'plural'
and attrvalue is not null
)
select article, word, plural
from m_and_n_nouns n
inner join
plurals p
on p.word_id = n.word_id
where
-- (word like '%er' and word not like '%ier') or
word like '%er'
/*
word like '%en' or
word like '%el' or
word like '%chen' or
word like '%lein'
*/
;
