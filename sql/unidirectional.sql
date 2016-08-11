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

/**
 *  Intuitively our graph is 'sparse' but lets look
 * quantify it. This is important as some algorithms
 * behave differently on sparse vs. dense graphs,
 * specifically shortest-path-algorithms.
**/

/**
 * We'll take some metrics on static aggregated graph first
 * and then see what we can say about windows
**/


/** 
 * Get the number of vertices, luckily author and coauthor
 * agree.
**/
SELECT count(distinct(author_id)) FROM coauthor_yearly;  
/* n = 1601589 */

SELECT count(distinct(coauthor_id)) FROM coauthor_yearly;  
/* n = 1601589 */

/**
 * Now get the number of edges
**/
SELECT count(*) FROM coauthor_unidi_yearly;  
/* m = 10335735 */

/**
 * A dense graph is a grpah in which the number of edges
 * is 'close' to the maximal number of edges... There is
 * disagreement on how close is 'close'. So lets
 * calcluate the Density of the graph and see if its an
 * issue:
 * 
 *   D =  _____2|E|_____ = 2m/(n(n-1)) = 8.058783e-06
 *         |V|(|V| - 1)
 * 
 * Clearly not. So this graph is sparse.
**/

/**
 * The graph is sparse, and so any graph containg a subset
 *  of these edges (as is the case for any windowed
 * graph) will be even more abjectly sparse.
**/

/**
 *  The following query gets the maximum density of any 
 * time slice
**/
  
SELECT max(density) FROM (
   SELECT count(*)/(1601589*1601588) as density
   FROM `coauthor_unidi_yearly`
   GROUP BY `year` ) 
as yearly_density;

/* => 0.000 */

/**
 * This returns a proportion so small that the maximum
 * density doesn't even register on SQL's precision. 
**/



