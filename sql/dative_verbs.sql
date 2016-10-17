use deutsch;

insert ignore into dative_verbs
select distinct word_id from mashup where pos_name = 'verb' and word in (
'begegnen',
'danken',
'dienen',
'drohen',
'folgen',
'gefallen',
'gehören',
'glauben',
'helfen',
'raten',
'schaden',
'vertrauen'
)
