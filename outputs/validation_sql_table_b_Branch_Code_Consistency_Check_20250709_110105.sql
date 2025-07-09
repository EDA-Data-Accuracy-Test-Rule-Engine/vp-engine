-- Validation Rule: Branch Code Consistency Check
-- Generated on: 2025-07-09T11:01:05.388556
-- Table: table_b
-- Status: PASS

WITH stats1 AS (
    SELECT COUNT(DISTINCT branch_code) as stat_value
    FROM public.table_a
    
),
stats2 AS (
    SELECT COUNT(DISTINCT branch_code) as stat_value
    FROM public.table_b
    
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
    'Branch Code Consistency Check' as rule_name,
    1 as total_rows,
    CASE WHEN status = 'FAIL' THEN 1 ELSE 0 END as failed_rows,
    CASE WHEN status = 'PASS' THEN 1 ELSE 0 END as passed_rows,
    status,
    table1_stat,
    table2_stat
FROM comparison;