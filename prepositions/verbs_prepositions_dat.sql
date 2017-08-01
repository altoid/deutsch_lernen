use deutsch;

insert ignore into verb_prep
select
'dat', v.verb_id, p.prep_id
from
(
    select
    distinct
    word verb, word_id verb_id
    from mashup m
    where pos_name = 'verb'
    and word in
    (
'abgeben',
'abhängen',
'anfangen',
'auffordern',
'aufhören',
'beginnen',
'bestehen',
'einladen',
'erziehen',
'erzählen',
'fehlen',
'folgen',
'fragen',
'führen',
'gehören',
'gratulieren',
'halten',
'handeln',
'hindern',
'hören',
'kommen',
'leben',
'leiden',
'liegen',
'meinen',
'passen',
'profitieren',
'rechnen',
'reden',
'riechen',
'rufen',
'schimpfen',
'schließen',
'schmecken',
'sehen',
'sprechen',
'teilnehmen',
'telefonieren',
'träumen',
'verbinden',
'vergleichen',
'verstehen',
'verwechseln',
'warnen',
'werden',
'wissen',
'wählen',
'zweifeln',
'zwingen',
'ändern',
'überreden'
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
'aus',
'mit',
'nach',
'unter',
'von',
'vor',
'zu',
'zwischen'
	)
) p
where
(verb = 'abgeben' and prep = 'von') or
(verb = 'abhängen' and prep = 'von') or
(verb = 'anfangen' and prep = 'mit') or
(verb = 'auffordern' and prep = 'zu') or
(verb = 'aufhören' and prep = 'mit') or
(verb = 'beginnen' and prep = 'mit') or
(verb = 'bestehen' and prep = 'aus') or
(verb = 'einladen' and prep = 'zu') or
(verb = 'erziehen' and prep = 'zu') or
(verb = 'erzählen' and prep = 'von') or
(verb = 'fehlen' and prep = 'an') or
(verb = 'folgen' and prep = 'aus') or
(verb = 'fragen' and prep = 'nach') or
(verb = 'führen' and prep = 'zu') or
(verb = 'gehören' and prep = 'zu') or
(verb = 'gratulieren' and prep = 'zu') or
(verb = 'halten' and prep = 'von') or
(verb = 'handeln' and prep = 'mit') or
(verb = 'handeln' and prep = 'von') or
(verb = 'hindern' and prep = 'an') or
(verb = 'hören' and prep = 'von') or
(verb = 'kommen' and prep = 'zu') or
(verb = 'leben' and prep = 'von') or
(verb = 'leiden' and prep = 'an') or
(verb = 'leiden' and prep = 'unter') or
(verb = 'liegen' and prep = 'an') or
(verb = 'meinen' and prep = 'zu') or
(verb = 'passen' and prep = 'zu') or
(verb = 'profitieren' and prep = 'von') or
(verb = 'rechnen' and prep = 'mit') or
(verb = 'reden' and prep = 'von') or
(verb = 'riechen' and prep = 'nach') or
(verb = 'rufen' and prep = 'nach') or
(verb = 'schimpfen' and prep = 'mit') or
(verb = 'schließen' and prep = 'aus') or
(verb = 'schmecken' and prep = 'nach') or
(verb = 'sehen' and prep = 'nach') or
(verb = 'sprechen' and prep = 'mit') or
(verb = 'sprechen' and prep = 'von') or
(verb = 'teilnehmen' and prep = 'an') or
(verb = 'telefonieren' and prep = 'mit') or
(verb = 'träumen' and prep = 'von') or
(verb = 'verbinden' and prep = 'mit') or
(verb = 'vergleichen' and prep = 'mit') or
(verb = 'verstehen' and prep = 'von') or
(verb = 'verwechseln' and prep = 'mit') or
(verb = 'warnen' and prep = 'vor') or
(verb = 'werden' and prep = 'zu') or
(verb = 'wissen' and prep = 'von') or
(verb = 'wählen' and prep = 'zu') or
(verb = 'wählen' and prep = 'zwischen') or
(verb = 'zweifeln' and prep = 'an') or
(verb = 'zwingen' and prep = 'zu') or
(verb = 'ändern' and prep = 'an') or
(verb = 'überreden' and prep = 'zu')
;

