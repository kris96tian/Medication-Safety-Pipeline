-- mart model: the final aggregated table that answers real questions
-- "which drugs have the most serious adverse events reported?"

with base as (
    select * from "drugdb"."analytics"."stg_drug_events"
),

summary as (
    select
        drug_name,

        count(*)                                                as total_reports,

        -- how many of those reports were flagged as serious
        count(*) filter (where severity = 'serious')            as serious_reports,

        -- percentage of reports that are serious , so useful for comparison
        round(
            count(*) filter (where severity = 'serious') * 100.0
            / nullif(count(*), 0),
        1)                                                      as pct_serious,

        -- average patient age across all reports for this drug
        round(avg(patient_age), 1)                              as avg_patient_age,

        -- top countries reporting issues with this drug
        mode() within group (order by country)                  as most_common_country,

        -- date range of the reports we have
        min(report_date)                                        as earliest_report,
        max(report_date)                                        as latest_report

    from base
    group by drug_name
)

select * from summary
order by total_reports desc