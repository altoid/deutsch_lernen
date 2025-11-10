with wordlist_counts as
(
    select wordlist_id, sum(c) lcount from
    (
        select wordlist_id, count(*) c
        from wordlist_unknown_word
        group by wordlist_id
        union all
        select wordlist_id, count(*) c
        from wordlist_known_word
        group by wordlist_id
    ) a
    group by wordlist_id
)
/*
select name, id wordlist_id, ifnull(lcount, 0) count, sqlcode
from wordlist
left join wordlist_counts wc on wc.wordlist_id = wordlist.id
where wordlist.id in (1315)
order by name
*/
select * from wordlist_counts
;


    select wordlist_id, sum(c) lcount from
    (
        select wordlist_id, count(*) c
        from wordlist_unknown_word
        group by wordlist_id
        union all
        select wordlist_id, count(*) c
        from wordlist_known_word
        group by wordlist_id
    ) a
    group by wordlist_id
;
