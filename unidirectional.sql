/**
 * This query creates a graph that has one 
 * edge for every publishing collaboration 
 * in a given year. The edge is weighted with
 * the number of publications that year.
*/
CREATE VIEW `coauthor_unidi_yearly` AS (
  SELECT *
  FROM `coauthor_yearly` `cay`
  WHERE `cay`.`author_id` < `cay`.`coauthor_id`
);
