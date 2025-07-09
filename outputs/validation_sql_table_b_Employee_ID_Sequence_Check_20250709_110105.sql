-- Validation Rule: Employee ID Sequence Check
-- Generated on: 2025-07-09T11:01:05.387100
-- Table: table_b
-- Status: PASS

WITH sequence_check AS (
    SELECT 
        id,
        LAG(id) OVER (ORDER BY id) as prev_value,
        ROW_NUMBER() OVER (ORDER BY id) as expected_sequence
    FROM table_b
    WHERE id IS NOT NULL
),
gaps AS (
    SELECT COUNT(*) as gap_count
    FROM sequence_check
    WHERE id != prev_value + 1 AND prev_value IS NOT NULL
)
SELECT 
    'Employee ID Sequence Check' as rule_name,
    (SELECT COUNT(*) FROM table_b) as total_rows,
    (SELECT gap_count FROM gaps) as failed_rows,
    (SELECT COUNT(*) FROM table_b) - (SELECT gap_count FROM gaps) as passed_rows,
    CASE 
        WHEN (SELECT gap_count FROM gaps) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END as status;