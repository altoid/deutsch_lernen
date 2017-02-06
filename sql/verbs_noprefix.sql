-- give me all the verbs that don't have separable prefixes

select
word_id,
word,
attrvalue as 2nd_person_sing,

substring(word, 1, char_length(word) - 2) inf_stem,
case
when attrvalue like '%est' then substring(attrvalue, 1, char_length(attrvalue) - 3)
when attrvalue like '%st'  then substring(attrvalue, 1, char_length(attrvalue) - 2)
when attrvalue like '%ßt'  then substring(attrvalue, 1, char_length(attrvalue) - 1)
else NULL
end as attrstem,


substring(word, 1, char_length(word) - 2) <>
case
when attrvalue like '%est' then substring(attrvalue, 1, char_length(attrvalue) - 3)
when attrvalue like '%st'  then substring(attrvalue, 1, char_length(attrvalue) - 2)
when attrvalue like '%ßt'  then substring(attrvalue, 1, char_length(attrvalue) - 1)
else NULL
end as irregular,

-- attrvalue like '%est',
-- attrvalue like '%st',
-- attrvalue like '%ßt',
-- attrvalue like '%sst',
1
from mashup
where attrkey = 'second_person_singular'
and pos_name = 'verb'
and not attrvalue regexp ' '
and word like '%en'
;
