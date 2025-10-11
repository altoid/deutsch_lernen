with words_in_lists as
(
select distinct word_id
from wordlist_known_word
where wordlist_id in (8,  48, 112,  68, 155, 135,  20)
),
words_having_attribute as
(
    select *
    from mashup_v
    where attrkey = 'plural'
    and attrvalue is not null    
)
select wha.*
from words_having_attribute wha
inner join words_in_lists wil
on wil.word_id = wha.word_id
-- order by wha.added desc
order by rand()
limit 11
;

