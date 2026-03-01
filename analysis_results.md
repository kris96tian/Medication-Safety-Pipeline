# Analysis Results - Drug Adverse Event Explorer

Data pulled from the OpenFDA public API. 7 drugs, 700 total reports.

---

## 1. Serious Report Rate per Drug

Amoxicillin has the highest serious report rate at 91%. Surprising for an antibiotic that most people consider pretty routine.

```sql
select drug_name, total_reports, serious_reports, pct_serious
from analytics.mart_drug_summary
order by pct_serious desc;
```

```
drug_name     | total_reports | serious_reports | pct_serious
--------------+---------------+-----------------+------------
amoxicillin   |           100 |              91 |        91.0
atorvastatin  |           100 |              88 |        88.0
ibuprofen     |           100 |              73 |        73.0
metformin     |           100 |              68 |        68.0
aspirin       |           100 |              66 |        66.0
lisinopril    |           100 |              56 |        56.0
omeprazole    |           100 |              56 |        56.0
```

---

## 2. Top 10 Adverse Reactions for Ibuprofen

Some of the rarer reactions like deep vein thrombosis and uterine perforation have a 100% serious rate, meaning every single report with that reaction was flagged as serious.

```sql
select reaction, report_count, pct_serious
from analytics.mart_reaction_frequency
where drug_name = 'ibuprofen'
order by report_count desc
limit 10;
```

```
reaction             | report_count | pct_serious
---------------------+--------------+------------
Pain                 |           15 |        73.3
Malaise              |            9 |        88.9
Weight decreased     |            8 |        87.5
Dyspnoea             |            7 |        85.7
Injury               |            7 |       100.0
Deep vein thrombosis |            6 |       100.0
Abdominal pain       |            6 |        83.3
Emotional distress   |            5 |       100.0
Uterine perforation  |            5 |       100.0
Fatigue              |            5 |        20.0
```

---

## 3. Average Patient Age per Drug

Lisinopril and Aspirin are mostly reported by patients over 60, which makes sense since both are commonly prescribed for heart related conditions. Ibuprofen sits much lower at 45.

```sql
select drug_name, avg_patient_age, most_common_country
from analytics.mart_drug_summary
order by avg_patient_age desc;
```

```
drug_name     | avg_patient_age | most_common_country
--------------+-----------------+--------------------
lisinopril    |            66.7 | US
aspirin       |            65.3 | US
metformin     |            63.4 | US
atorvastatin  |            63.0 | US
omeprazole    |            62.7 | US
amoxicillin   |            57.8 | US
ibuprofen     |            45.1 | US
```

---

## 4. Reports by Country (Top 10)

The US makes up 70% of all reports. This is probably more about how well the FDA reporting system works than about Americans having more drug problems.

```sql
select country, count(*) as total_reports
from raw_drug_events
where country is not null
group by country
order by total_reports desc
limit 10;
```

```
country | total_reports
--------+--------------
US      |           492
GB      |            93
IT      |            20
DE      |            16
FR      |            11
BR      |             8
ES      |             7
CN      |             6
BD      |             5
JP      |             5
```

---

## 5. Reports by Sex per Drug

Ibuprofen and Atorvastatin have way more female reporters than male. Aspirin and Amoxicillin are pretty much 50/50.

```sql
select drug_name, patient_sex, count(*) as reports
from analytics.stg_drug_events
where patient_sex != 'unknown'
group by drug_name, patient_sex
order by drug_name, reports desc;
```

```
drug_name     | patient_sex | reports
--------------+-------------+--------
amoxicillin   | male        |      55
amoxicillin   | female      |      41
aspirin       | male        |      51
aspirin       | female      |      47
atorvastatin  | female      |      67
atorvastatin  | male        |      31
ibuprofen     | female      |      68
ibuprofen     | male        |      31
lisinopril    | female      |      50
lisinopril    | male        |      46
metformin     | female      |      55
metformin     | male        |      40
omeprazole    | female      |      55
omeprazole    | male        |      40
```

---

## 6. Serious Events by Age Group

Over 60 accounts for almost half of all reports. The under 18 group is small (only 16 reports) but 14 of those were serious.

```sql
select
    case
        when patient_age < 18 then 'under 18'
        when patient_age between 18 and 40 then '18-40'
        when patient_age between 41 and 60 then '41-60'
        when patient_age > 60 then 'over 60'
        else 'unknown'
    end as age_group,
    count(*) as total,
    count(*) filter (where severity = 'serious') as serious
from analytics.stg_drug_events
group by age_group
order by total desc;
```

```
age_group | total | serious
----------+-------+--------
over 60   |   322 |     233
41-60     |   165 |     132
unknown   |   135 |      69
18-40     |    62 |      50
under 18  |    16 |      14
```

---

## 7. Reactions That Show Up Across All 7 Drugs

These reactions are not tied to one specific drug. They appear in reports for all 7 medications in the dataset. Fatigue and drug interaction are at the top.

```sql
select reaction, count(distinct drug_name) as appears_in_n_drugs, sum(report_count) as total_reports
from analytics.mart_reaction_frequency
group by reaction
order by appears_in_n_drugs desc, total_reports desc
limit 15;
```

```
reaction                  | appears_in_n_drugs | total_reports
--------------------------+--------------------+--------------
Fatigue                   |                  7 |            47
Drug interaction          |                  7 |            44
Dyspnoea                  |                  7 |            43
Nausea                    |                  7 |            41
Diarrhoea                 |                  7 |            40
Headache                  |                  7 |            39
Pain                      |                  7 |            38
Dizziness                 |                  7 |            34
Anaemia                   |                  7 |            30
Vomiting                  |                  7 |            26
Rash                      |                  7 |            24
Platelet count decreased  |                  7 |            23
Insomnia                  |                  7 |            22
Weight decreased          |                  7 |            22
Pain in extremity         |                  7 |            21
```
