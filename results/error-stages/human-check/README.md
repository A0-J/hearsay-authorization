# Human check of the error coding (prepared 2026-11-17; to be filled by a person)

Every code so far is a model's: coders A and B were instances of the same Claude model as the assistant, and the
adjudication and the "manual" samples were the assistant's. This is the first human reference.

## What to do

1. Read CODEBOOK.md. Do not open coded_final.csv, adjudication.csv, model_coding*.csv, errors_coded.csv,
   manual_sample*.csv or key.csv before you finish (they hold model labels or point to them).
2. Fill the `h_*` columns of sheet_errors.csv (60 rows) with the allowed values. `h_note` is optional.
3. Optionally fill sheet_ad_approvals.csv (34 rows; short reasons).
4. Run `python experiments/human_check_agreement.py`.

## Analysis fixed before any human code

- Agreement of the human codes with the final model codes (coded_final.csv): Cohen's kappa and raw agreement for
  evidence_reading, reason_conclusion, driver, timing_misread and the derived stage; overall and per setting
  (settings never pooled).
- E1 / gpt-4.1 (30 rows, a simple random sample of the 123 errors): the share of `read_correctly_decided_wrong`
  by the human, with a Wilson 95% interval, next to the model codes' share on the same 30 rows and on all 123.
  The human share is the estimate to report for "read the evidence correctly and still decided wrong"; the model
  share is reported as model-assisted.
- AgentDojo sheet: counts of h_source_named and h_presents_id_as_record, next to the mechanical rule in
  results/invalid-approvals/REPORT.md.
- Nothing is dropped or recoded after the human codes are seen. If a row is unreadable, write `unreadable` in
  h_note and leave its codes empty; it is reported as missing.
