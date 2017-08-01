use deutsch;


create temporary table preposition_verb_list_t
(
		word varchar(64) collate utf8_unicode_ci not null primary key
) engine=innodb default charset=utf8 collate utf8_swedish_ci
;

insert ignore into preposition_verb_list_t values
('abgeben'),
('abhängen'),
('abstimmen'),
('achten'),
('anfangen'),
('ankommen'),
('antworten'),
('auffordern'),
('aufhören'),
('aufpassen'),
('aufregen'),
('auseinandersetzen'),
('ausgeben'),
('bedanken'),
('beginnen'),
('bemühen'),
('beraten'),
('berichten'),
('beschließen'),
('beschweren'),
('beschäftigen'),
('bestehen'),
('bewerben'),
('beziehen'),
('bitten'),
('danken'),
('denken'),
('diskutieren'),
('drehen'),
('eignen'),
('einladen'),
('entscheiden'),
('entschließen'),
('entschuldigen'),
('entwickeln'),
('erholen'),
('erinnern'),
('erkundigen'),
('ersetzen'),
('erziehen'),
('erzählen'),
('fehlen'),
('folgen'),
('fragen'),
('freuen'),
('führen'),
('fürchten'),
('gehen'),
('gehören'),
('gewöhnen'),
('glauben'),
('gratulieren'),
('halten'),
('handeln'),
('hindern'),
('hoffen'),
('hören'),
('hüten'),
('informieren'),
('interessieren'),
('irren'),
('klagen'),
('kommen'),
('kämpfen'),
('kümmern'),
('lachen'),
('leben'),
('leiden'),
('liegen'),
('lächeln'),
('meinen'),
('melden'),
('nachdenken'),
('passen'),
('profitieren'),
('protestieren'),
('reagieren'),
('rechnen'),
('reden'),
('richten'),
('riechen'),
('rufen'),
('schimpfen'),
('schließen'),
('schmecken'),
('schützen'),
('sehen'),
('sehnen'),
('sein'),
('sorgen'),
('sprechen'),
('stehen'),
('stimmen'),
('streiten'),
('teilnehmen'),
('telefonieren'),
('treffen'),
('trennen'),
('träumen'),
('tun'),
('unterhalten'),
('unterrichten'),
('unterscheiden'),
('verabreden'),
('verbinden'),
('vergleichen'),
('verlassen'),
('verlieben'),
('verloben'),
('vermieten'),
('verstehen'),
('verwechseln'),
('verzichten'),
('vorbereiten'),
('warnen'),
('warten'),
('wenden'),
('werden'),
('wissen'),
('wundern'),
('wählen'),
('zweifeln'),
('zwingen'),
('ändern'),
('ärgern'),
('überreden')
;

