use deutsch;

create or replace view preposition_case_v as
select *, 'dative' `case`
from dative_preposition_v

union

select *, 'accusative' `case`
from accusative_preposition_v

union

select *, 'genitive' `case`
from genitive_preposition_v

union

select *, 'accusative/dative' `case`
from acc_dat_preposition_v
;
