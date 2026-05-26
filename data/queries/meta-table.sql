-- Create meta-table (named "a_meta_table so it shows up first alphabetically.)
CREATE TABLE a_meta_table (
    table_name TEXT PRIMARY KEY,
    country TEXT
);

--Grab a list of ll the tables & the country
INSERT INTO a_meta_table (table_name, country)
SELECT 
    name,
    substr(name, 1, instr(name, '_table_') - 1)
FROM sqlite_master
WHERE type = 'table';

--set up columns for analysis
ALTER TABLE a_meta_table ADD COLUMN row_count INTEGER;
ALTER TABLE a_meta_table ADD COLUMN column_count INTEGER;
ALTER TABLE a_meta_table ADD COLUMN category_guess TEXT;