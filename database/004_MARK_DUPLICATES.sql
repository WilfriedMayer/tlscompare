-- 1) Create Table of Rules
--      where http url (without 'http') equals https url (without 'https')
--      and there is more of one rule
--      also select the first rule with min(id) (because this will not be marked duplicate)
-- 2) Mark Duplicates (All except the first)
-- 3) Drop the Table


create table dominik_duplicates as
SELECT http_url, https_url, min(id) as min, count(*) as c from comparisons
  where substr(http_url, 8) = substr(https_url, 9)
group by http_url, https_url
having count(*) > 1;


update comparisons
set code = 'D_DUPLICATE'
where id in (
            select id
            from comparisons c join dominik_duplicates d
                on (c.http_url = d.http_url
                    and c.https_url = d.https_url
                    and c.id != d.min));

DROP TABLE dominik_duplicates;