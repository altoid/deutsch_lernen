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
    in (select vorsilbe from trennbar_vorsilbe
)
and length(prefix.word) > length(noprefix.word)
and right(prefix.word, length(noprefix.word)) = noprefix.word

order by 
 left(prefix.word, length(prefix.word) - length(noprefix.word)),
 noprefix.word
-- prefix.word

;
