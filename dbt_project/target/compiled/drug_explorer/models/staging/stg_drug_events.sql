-- staging model: take the raw messy data and clean it up a bit
-- this is the "transform" part of ETL
-- we cast types, rename things, and decode the fda codes into readable values

with source as (
    -- just pull everything from the raw table
    select * from raw_drug_events
),

cleaned as (
    select
        report_id,
        lower(trim(drug_name))                          as drug_name,

        -- fda sends dates as strings like "20230115", convert to real date
        to_date(receive_date, 'YYYYMMDD')               as report_date,

        -- fda uses 1/2 codes for serious, make it readable
        case serious
            when '1' then 'serious'
            when '2' then 'not serious'
            else 'unknown'
        end                                             as severity,

        country,

        -- age comes as text, cast to number (some values are null or weird)
        nullif(patient_age, '')::numeric                as patient_age,

        -- fda uses 1/2 for sex
        case patient_sex
            when '1' then 'male'
            when '2' then 'female'
            else 'unknown'
        end                                             as patient_sex,

        reactions,
        loaded_at

    from source
    -- filter out rows with no report id (bad data)
    where report_id is not null
)

select * from cleaned