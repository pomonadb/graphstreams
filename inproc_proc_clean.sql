/* 
This set of sql commands nullifies records from inproceedings
that do not have key-foreign key relationship between
inproceedings.crossref and proceedings.key.

There are 223 / 1,744,253 such records (.012%). 
*/

/* Set bad foreign keys to null */
UPDATE `inproceedings`
  SET `inproceedings`.`crossref` = NULL
WHERE
  `inproceedings.`crossref` NOT IN
    (SELECT `key` FROM `proceedings`);

/* Create foreign key */
ALTER TABLE inproceedings 
  ADD FOREIGN KEY (`crossref`)
    REFERENCES `proceedings` (`key`)
    ON DELETE SET NULL
    ON UPDATE CASCADE;
