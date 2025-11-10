use deutsch;

-- get me all of the data for a word and all of the semantic info on parts of speech.

with pos_info as
(
select
    p.id pos_id,
    p.name pos_name,
    a.id attribute_id,
    a.attrkey,
    pf.sort_order
from pos p
inner join pos_form pf on pf.pos_id = p.id
inner join attribute a on a.id = pf.attribute_id
)
select
        case
        when mashup_v.attrvalue_id is not null then
        concat(pos_info.attrkey, '-', mashup_v.attrvalue_id)
        else pos_info.attrkey
        end
        field_key,
        case
        when mashup_v.word_id is not null then
        concat(mashup_v.word_id, '-', pos_info.pos_id)
        else pos_info.pos_id
        end tag,
        pos_info.pos_name,
        pos_info.sort_order,
        pos_info.attrkey,
        mashup_v.word,
        mashup_v.attrvalue
from pos_info
left join  mashup_v on mashup_v.pos_id = pos_info.pos_id and mashup_v.attribute_id = pos_info.attribute_id
and mashup_v.word is null
;

