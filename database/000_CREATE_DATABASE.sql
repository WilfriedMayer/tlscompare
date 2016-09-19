DROP TABLE comparisons;
DROP TABLE results;

CREATE TABLE comparisons (
	id INTEGER NOT NULL,
	http_url VARCHAR,
	https_url VARCHAR,
	similarityvalue1 FLOAT,
	similarityvalue2 FLOAT,
	http_url_id INTEGER,
	https_url_id INTEGER,
	rank INTEGER,
	code VARCHAR,
	PRIMARY KEY (id)
);

CREATE TABLE results (
	id INTEGER NOT NULL,
	uid VARCHAR,
	ip VARCHAR,
	useragent VARCHAR,
	req_time DATETIME,
	res_time DATETIME,
	validity BOOLEAN,
	comparison_id INTEGER,
	PRIMARY KEY (id),
	CHECK (validity IN (0, 1)),
	FOREIGN KEY(comparison_id) REFERENCES comparisons (id)
);

-- DONT FORGET TO IMPORT THE DATA
-- IMPORT DATA

-- .mode csv
-- .separator ;
-- .import ../files/all_with_ids_and_code.csv comparisons

--- ```
--- awk 'NR>1{print NR-1";"$0";"}' all.csv > all_with_id_and_code.csv
--- ```