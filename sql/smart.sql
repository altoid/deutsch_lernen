-- wordlist id = 113
-- select id word_id from word where date(added) = '2015-03-22';

select distinct word_id
from mashup
where pos_name = 'verb'
and word like '%nehm%'



