select name, id wordlist_id, ifnull(lcount, 0) count
from wordlist
left join
(
    select wordlist_id, sum(c) lcount
    from
    (
        select wordlist_id, count(*) c
        from wordlist_unknown_word
        group by wordlist_id
        union
        select wordlist_id, count(*) c
        from wordlist_known_word
        group by wordlist_id
    ) a
    group by wordlist_id
) b on b.wordlist_id = wordlist.id
order by name
;
