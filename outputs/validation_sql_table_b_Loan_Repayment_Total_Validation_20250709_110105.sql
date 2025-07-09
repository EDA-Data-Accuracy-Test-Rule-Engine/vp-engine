-- Validation Rule: Loan Repayment Total Validation
-- Generated on: 2025-07-09T11:01:05.389663
-- Table: table_b
-- Status: FAIL

WITH stats1 AS (
    SELECT (SUM(overdue_principal_payment) + SUM(overdue_principal_penalty) + SUM(overdue_interest_payment) + SUM(overdue_interest_penalty)) as stat_value
    FROM public.overdue_loan_payments
    WHERE contract_nbr IS NOT NULL
),
stats2 AS (
    SELECT SUM(repayment_amount) as stat_value
    FROM public.transaction_summary
    WHERE contract_nbr IS NOT NULL
),
comparison AS (
    SELECT 
        s1.stat_value as table1_stat,
        s2.stat_value as table2_stat,
        CASE 
            WHEN s1.stat_value = s2.stat_value THEN 'PASS'
            ELSE 'FAIL'
        END as status
    FROM stats1 s1, stats2 s2
)
SELECT 
    'Loan Repayment Total Validation' as rule_name,
    1 as total_rows,
    CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END as failed_rows,
    CASE WHEN status = 'PASS' THEN 1 ELSE 0 END as passed_rows,
    status,
    table1_stat,
    table2_stat
FROM comparison;