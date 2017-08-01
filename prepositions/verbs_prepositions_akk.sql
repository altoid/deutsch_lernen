use deutsch;

insert ignore into verb_prep
select
'akk', v.verb_id, p.prep_id
from
(
    select
    distinct
    word verb, word_id verb_id
    from mashup m
    where pos_name = 'verb'
    and word in
    (
    'abstimmen',
    'achten',
    'ankommen',
    'antworten',
    'aufpassen',
    'ausgeben',
    'beraten',
    'berichten',
    'beschließen',
    'bitten',
    'danken',
    'denken',
    'diskutieren',
    'erinnern',
    'ersetzen',
    'folgen',
    'gehen',
    'glauben',
    'halten',
    'hoffen',
    'hören',
    'informieren',
    'klagen',
    'kommen',
    'kämpfen',
    'lachen',
    'lächeln',
    'nachdenken',
    'protestieren',
    'reagieren',
    'reden',
    'schimpfen',
    'sein',
    'sorgen',
    'sprechen',
    'stehen',
    'stimmen',
    'streiten',
    'tun',
    'unterrichten',
    'vermieten',
    'verzichten',
    'warten',
    'wählen'
    )
) v,
(
    select
    distinct
    word prep, word_id prep_id
    from mashup m
    where pos_name = 'preposition'
    and word in
    (
    'an',
    'auf',
    'durch',
    'für',
    'gegen',
    'in'
    'um',
    'über'
    )
) p
where
(verb = 'abstimmen' and prep = 'über') or
(verb = 'achten' and prep = 'auf') or
(verb = 'ankommen' and prep = 'auf') or
(verb = 'antworten' and prep = 'auf') or
(verb = 'aufpassen' and prep = 'auf') or
(verb = 'ausgeben' and prep = 'für') or
(verb = 'beraten' and prep = 'über') or
(verb = 'berichten' and prep = 'über') or
(verb = 'beschließen' and prep = 'über') or
(verb = 'bitten' and prep = 'um') or
(verb = 'danken' and prep = 'für') or
(verb = 'denken' and prep = 'an') or
(verb = 'diskutieren' and prep = 'über') or
(verb = 'erinnern' and prep = 'an') or
(verb = 'ersetzen' and prep = 'durch') or
(verb = 'folgen' and prep = 'auf') or
(verb = 'gehen' and prep = 'um') or
(verb = 'glauben' and prep = 'an') or
(verb = 'halten' and prep = 'für') or
(verb = 'hoffen' and prep = 'auf') or
(verb = 'hören' and prep = 'auf') or
(verb = 'informieren' and prep = 'über') or
(verb = 'klagen' and prep = 'über') or
(verb = 'kommen' and prep = 'auf') or
(verb = 'kämpfen' and prep = 'für') or
(verb = 'kämpfen' and prep = 'gegen') or
(verb = 'kämpfen' and prep = 'um') or
(verb = 'lachen' and prep = 'über') or
(verb = 'lächeln' and prep = 'über') or
(verb = 'nachdenken' and prep = 'über') or
(verb = 'protestieren' and prep = 'gegen') or
(verb = 'reagieren' and prep = 'auf') or
(verb = 'reden' and prep = 'über') or
(verb = 'schimpfen' and prep = 'über') or
(verb = 'sein' and prep = 'für') or
(verb = 'sein' and prep = 'gegen') or
(verb = 'sorgen' and prep = 'für') or
(verb = 'sprechen' and prep = 'über') or
(verb = 'stehen' and prep = 'auf') or
(verb = 'stimmen' and prep = 'für') or
(verb = 'stimmen' and prep = 'gegen') or
(verb = 'streiten' and prep = 'über') or
(verb = 'tun' and prep = 'für') or
(verb = 'unterrichten' and prep = 'über') or
(verb = 'vermieten' and prep = 'an') or
(verb = 'verzichten' and prep = 'auf') or
(verb = 'warten' and prep = 'auf') or
(verb = 'wählen' and prep = 'in')

;