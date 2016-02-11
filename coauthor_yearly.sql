/**
  This create the View Related to the coauthorship table,
  allowing for a more fine-grained temporal analysis.
*/
CREATE VIEW `coauthor_yearly` AS
  SELECT `ca`.`author_id` AS `author_id`,
         `ca`.`coauthor_id` AS `coauthor_id`,
          `p`.`year` AS `year`,
          count(distinct(`p`.`eid` )) AS `num_pubs`
  FROM  `co_author` `ca`, `publications` `p`
  WHERE `p`.`eid` = `ca`.`entity_id`
  GROUP BY `ca`.`author_id`,`ca`.`coauthor_id`, `p`.`year`;
 
