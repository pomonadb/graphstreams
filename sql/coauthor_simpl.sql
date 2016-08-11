/**
   This SQL statement create the coauthor_simpl
   view that represents the first time they
   collaborated as well as a weight that
   represents the number of collaborations
   the two authors have had.
*/
CREATE VIEW `coauthor_simpl` AS (
  SELECT `ca`.`author_id` AS `author_id`,
         `ca`.`coauthor_id` AS `coauthor_id`,
          min(`p`.`year`) AS `year`,
          count(distinct(`p`.`eid` )) AS `num_pubs`  
  FROM  `co_author` `ca`, `publications` `p` 
  WHERE `p`.`eid` = `ca`.`entity_id` 
  GROUP BY `ca`.`author_id`,`ca`.`coauthor_id`);

/* This will load the whole table.  Should be
   something like 14,463,860 */
SELECT count(*) FROM coauthor_simpl;
