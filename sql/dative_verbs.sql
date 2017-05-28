use deutsch;

insert ignore into dative_verb
select distinct word_id from mashup where pos_name = 'verb' and word in (
'begegnen',
'danken',
'dienen',
'drohen',
'einfallen',
'folgen',
'gefallen',
'gehören',
'glauben',
'gleichen',
'gratulieren',
'helfen',
'imponieren',
'lauschen',
'passen',
'raten',
'schaden',
'schmecken',
'stehen',
'trauen',
'vertrauen'
)
