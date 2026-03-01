-- mart model: which reactions show up most often per drug
-- reactions in the raw data come as a comma-separated string
-- we unnest them here so each reaction gets its own row

with base as (
    select * from "drugdb"."analytics"."stg_drug_events"
),

-- split the commaseparated reactions into individual rows
unnested as (
    select
        drug_name,
        severity,
        trim(reaction_term)     as reaction
    from base,
    -- unnest splits "nausea, headache, vomiting" into 3 separate rows
    lateral unnest(string_to_array(reactions, ',')) as reaction_term
    where reactions is not null and reactions != ''
),

aggregated as (
    select
        drug_name,
        reaction,
        count(*)                as report_count,
        -- what share of reactions for this drug are serious
        round(
            count(*) filter (where severity = 'serious') * 100.0
            / nullif(count(*), 0),
        1)                      as pct_serious

    from unnested
    -- skip empty strings after trimming
    where length(trim(reaction)) > 0
    group by drug_name, reaction
)

select * from aggregated
order by drug_name, report_count desc