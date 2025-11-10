update wordlist
set `name` = case when %(name)s is not null and length(%(name)s) > 0
                then %(name)s
                else name
            end,
set citation = case when %(citation)s is not null and length(%(citation)s) > 0
                then %(citation)s
                else citation
            end,
set sqlcode = case when %(sqlcode)s is not null and length(%(sqlcode)s) > 0
                then %(sqlcode)s
                else sqlcode
            end,
set notes = case when %(notes)s is not null and length(%(notes)s) > 0
                then %(notes)s
                else notes
            end
where id = 585
;

