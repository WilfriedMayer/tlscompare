CREATE TABLE everywhere
(
    http_url TEXT NOT NULL,
    https_url TEXT NOT NULL,
    comment TEXT NOT NULL
);

-- sqlite> .mode csv
-- sqlite> .separator ;
-- sqlite> .import https_everywhere_generated_rules_try_20150715.csv everywhere

ALTER TABLE comparisons ADD comment VARCHAR;

INSERT INTO comparisons ( http_url, https_url, code, comment )
  SELECT http_url, https_url, 'H', comment
  FROM everywhere;

DROP TABLE everywhere;