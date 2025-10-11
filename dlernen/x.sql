WITH
attrs_for_quiz AS
  (
             SELECT     qs.quiz_id,
                        qs.attribute_id
             FROM       quiz
             INNER JOIN quiz_structure qs
             ON         quiz.id = qs.quiz_id
             WHERE      quiz_key = %s ),

testable_attrs_and_values AS
  (
             SELECT     a.*,
                        m.attrkey,
                        m.word_id,
                        m.word,
                        m.attrvalue
             FROM       attrs_for_quiz a
             INNER JOIN mashup_v m
             ON         a.attribute_id = m.attribute_id
             INNER JOIN wordlist_known_word wkw
             ON         m.word_id = wkw.word_id
             WHERE      attrvalue IS NOT NULL
             AND        wkw.wordlist_id IN (%s) ),
q1 AS
  (
            -- word has been presented 5 or fewer times (or not at all)
            SELECT    'QUERY1' qname,
                      ta.quiz_id,
                      ta.attribute_id,
                      ta.attrkey,
                      ta.word_id,
                      ta.word,
                      ta.attrvalue,
                      ifnull(v.presentation_count, 0) presentation_count,
                      ifnull(v.correct_count, 0)      correct_count,
                      v.last_presentation
            FROM      testable_attrs_and_values ta
            LEFT JOIN quiz_v v
            ON        ta.word_id = v.word_id
            AND       ta.quiz_id = v.quiz_id
            AND       ta.attribute_id = v.attribute_id
            WHERE     ifnull(presentation_count, 0) <= 5 ),
q2 AS
  (
             -- crappy score (<= 80% in 10 or more presentations
             SELECT     'QUERY2' qname,
                        ta.quiz_id,
                        ta.attribute_id,
                        ta.attrkey,
                        ta.word_id,
                        ta.word,
                        ta.attrvalue,
                        ifnull(v.presentation_count, 0) presentation_count,
                        ifnull(v.correct_count, 0)      correct_count,
                        v.last_presentation
             FROM       testable_attrs_and_values ta
             INNER JOIN quiz_v v
             ON         ta.word_id = v.word_id
             AND        ta.quiz_id = v.quiz_id
             AND        ta.attribute_id = v.attribute_id
             WHERE      presentation_count >= 10
             AND        correct_count / presentation_count <= 0.80 ),
q3 AS
  (
             -- word hasn't been quizzed in more than 30 days
             SELECT     'QUERY3' qname,
                        ta.quiz_id,
                        ta.attribute_id,
                        ta.attrkey,
                        ta.word_id,
                        ta.word,
                        ta.attrvalue,
                        ifnull(v.presentation_count, 0) presentation_count,
                        ifnull(v.correct_count, 0)      correct_count,
                        v.last_presentation
             FROM       testable_attrs_and_values ta
             INNER JOIN quiz_v v
             ON         ta.word_id = v.word_id
             AND        ta.quiz_id = v.quiz_id
             AND        ta.attribute_id = v.attribute_id
             WHERE      curdate() - INTERVAL 30 day > last_presentation ),
alle AS
  (
         SELECT *
         FROM   q1
         UNION
         SELECT *
         FROM   q2
         UNION
         SELECT *
         FROM   q3 )

SELECT   alle.*
FROM     alle
ORDER BY rand()
LIMIT    1
