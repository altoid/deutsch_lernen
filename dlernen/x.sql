    with matching as ( select id word_id from word where word = 'geben' )
    select word_id
    from matching
;
