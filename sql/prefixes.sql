-- compare verbs with and without their separable prefixes

select
		noprefix.*,
        left(prefix.word, length(prefix.word) - length(noprefix.word)) prefix,
		prefix.*
from (
        select 
			   word, attrvalue definition
        from
				mashup
        
        where 1
        and	  pos_name = 'verb'
        and	  attrkey = 'definition'
		) prefix,
		(
        select 
			   word, attrvalue definition
        from
				mashup
        
        where 1
        and	  pos_name = 'verb'
        and	  attrkey = 'definition'
		) noprefix

where 1
and left(prefix.word, length(prefix.word) - length(noprefix.word))
    in (
        'ab',
        'an',
        'auf',
        'aus',
        'be',
        'ent',
        'er',
        'fest',
        'ge',
        'heraus',
        'herum',
        'hin',
        'hinunter',
        'los',
        'mit',
        'nach',
        'rein',
        'statt',
        'über',
        'um',
        'unter',
        'ver',
        'vor',
        'weg',
        'wider',
        'wieder',
        'zer',
        'zu',
        'züruck'
)
and length(prefix.word) > length(noprefix.word)
and right(prefix.word, length(noprefix.word)) = noprefix.word

order by 
 noprefix.word,
left(prefix.word, length(prefix.word) - length(noprefix.word))

;
