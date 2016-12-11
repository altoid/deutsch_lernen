use deutsch;

insert ignore into dative_preposition
select distinct word_id from mashup where pos_name = 'preposition' and word in (
'aus',
'außer',
'bei',
'mit',
'nach',
'seit',
'von',
'zu'
);

insert ignore into accusative_preposition
select distinct word_id from mashup where pos_name = 'preposition' and word in (
'bis',
'durch',
'für',
'gegen',
'ohne',
'wider',
'um'
)
;

insert ignore into genitive_preposition
select distinct word_id from mashup where pos_name = 'preposition' and word in (
'trotz',
'während',
'statt',
'anstatt',
'wegen'
)
;

insert ignore into acc_dat_preposition
select distinct word_id from mashup where pos_name = 'preposition' and word in (
'an',
'auf',
'hinter',
'in',
'neben',
'über',
'unter',
'vor',
'zwischen'
)
;

/*
this is a simple check to make sure we didn't miss any words:

select mashup.word_id, p.word_id 
from mashup 
left join preposition_case_v p on mashup.word_id = p.word_id
where mashup.pos_id = 7
;
*/

