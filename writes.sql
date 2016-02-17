-- Creates the writes relationships using the disambiguated person id

INSERT INTO writes (author_id, entity_id)
SELECT DISTINCT person.eid,
                pub.eid
FROM alias_writes w1,
     alias_writes w2,
     person,
     publication pub W HERE w1.entity_id = person.eid
AND w1.author_id = w2.author_id
AND w2.entity_id = pub.eid;
