use deutsch;

with list_count as
(
select
    wordlist_id, count(*) wordlist_count
from wordlist_word
group by wordlist_id
)
select
    wl.id wordlist_id,
    wl.name,
    case
        when wl.sqlcode is not null then 'smart'
        when lc.wordlist_count is null then 'empty'
        else 'standard'
    end list_type
from wordlist wl
left join list_count lc
on lc.wordlist_id = wl.id
-- where wl.id in (49,51,54,81)
;
