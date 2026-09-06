DELIMITER $$

DROP PROCEDURE IF EXISTS `sp_r_denormalizeddata` $$
CREATE PROCEDURE `sp_r_denormalizeddata`
(IN `entity` VARCHAR(10) DEFAULT 'ALL',
 IN `accuracy` INT DEFAULT 99)
COMMENT 'Denormalize KEYSTONE data'
MODIFIES SQL DATA
BEGIN
    DECLARE entity_filter BIGINT;
    DECLARE sql_stmt VARCHAR(65535);
    DECLARE i INT DEFAULT 1;

    -- Determine the entity filter
    IF entity = 'ALL' THEN
        SET entity_filter = NULL;
    ELSE
        SET entity_filter = CAST(entity AS BIGINT);
    END IF;

    -- Validate accuracy parameter
    IF accuracy <= 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Accuracy must be a positive integer';
    END IF;

    -- Create a temporary table to store the results
    DROP TEMPORARY TABLE IF EXISTS tt_sp_r_denormalizeddata;
    CREATE TEMPORARY TABLE tt_sp_r_denormalizeddata (
        KID BIGINT,
        TID BIGINT
    );

    -- Insert data into the temporary table
    IF entity_filter IS NULL THEN
        INSERT INTO tt_sp_r_denormalizeddata (KID, TID)
        SELECT KID, TID FROM T01;
    ELSE
        INSERT INTO tt_sp_r_denormalizeddata (KID, TID)
        SELECT KID, TID FROM T01 WHERE TID = entity_filter;
    END IF;

    -- Initialize session variables for row numbering
    SET @row_num := 0, @prev_EID := NULL;

    -- Recursive CTE to handle UNV relationships and sub-data
    WITH RECURSIVE CTE_UNV AS (
        -- Anchor member: start with primary T01 records having non-null T02-UNVs
        SELECT 
            T01.KID, 
            T02.EID, 
            T02.UNV, 
            1 AS level
        FROM 
            T01
        JOIN 
            T02 ON T01.KID = T02.EID
        WHERE 
            T02.UNV IS NOT NULL
        
        UNION ALL
        
        -- Recursive member: join secondary T01 records
        SELECT 
            T01.KID, 
            T02.EID, 
            T02.UNV, 
            CTE_UNV.level + 1 AS level
        FROM 
            CTE_UNV
        JOIN 
            T02 ON CTE_UNV.UNV = T02.EID
        JOIN 
            T01 ON T02.EID = T01.KID
        WHERE 
            CTE_UNV.level < accuracy
    )
    
    -- Dynamically create columns for denormalized AID/value instances from T02, T03, and T04
    SET @sql_stmt = 'SELECT ';
    WHILE i <= accuracy DO
        SET @sql_stmt = CONCAT(@sql_stmt, 
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T02.AID END) AS T2AID_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T02.INV END) AS T2INV_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T02.NMV END) AS T2NMV_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T02.BOV END) AS T2BOV_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T02.UNV END) AS T2UNV_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T03.AID END) AS T3AID_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T03.TXV END) AS T3TXV_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T04.AID END) AS T4AID_', i, ', ',
            'MAX(CASE WHEN aid_rank = ', i, ' THEN T04.LTV END) AS T4LTV_', i, ', ');
        SET i = i + 1;
    END WHILE;

    -- Recurse on UNV to extract related entities and their columns
    SET i = 1;
    WHILE i <= accuracy DO
        SET @sql_stmt = CONCAT(@sql_stmt, 
            'MAX(CASE WHEN unv_rank = ', i, ' THEN T02.UNV END) AS T2UNV_', i, ', ',
            'MAX(CASE WHEN unv_rank = ', i, ' THEN T03.UNV END) AS T3UNV_', i, ', ',
            'MAX(CASE WHEN unv_rank = ', i, ' THEN T04.UNV END) AS T4UNV_', i, ', ');
        SET i = i + 1;
    END WHILE;

    -- Add dates from T01 and complete the SELECT clause with KID and TID
    SET @sql_stmt = CONCAT(@sql_stmt, 
        'T01.SDT AS StartDate, T01.EDT AS EndDate, ',
        'KID, TID FROM tt_sp_r_denormalizeddata ');

    -- Join with T02, T03, T04, and T01, and with CTE_UNV
    SET @sql_stmt = CONCAT(@sql_stmt, 
        'LEFT JOIN (SELECT EID, AID, INV, NMV, BOV, UNV, @row_num := IF(@prev_EID = EID, @row_num + 1, 1) AS aid_rank, @prev_EID := EID ',
        'FROM T02, (SELECT @row_num := 0, @prev_EID := NULL) AS init) AS T02 ON T02.EID = tt_sp_r_denormalizeddata.KID ',
        'LEFT JOIN (SELECT EID, AID, TXV, @row_num := IF(@prev_EID = EID, @row_num + 1, 1) AS aid_rank, @prev_EID := EID ',
        'FROM T03, (SELECT @row_num := 0, @prev_EID := NULL) AS init) AS T03 ON T03.EID = tt_sp_r_denormalizeddata.KID ',
        'LEFT JOIN (SELECT EID, AID, LTV, @row_num := IF(@prev_EID = EID, @row_num + 1, 1) AS aid_rank, @prev_EID := EID ',
        'FROM T04, (SELECT @row_num := 0, @prev_EID := NULL) AS init) AS T04 ON T04.EID = tt_sp_r_denormalizeddata.KID ',
        'LEFT JOIN T01 ON T01.KID = tt_sp_r_denormalizeddata.KID ',
        'LEFT JOIN CTE_UNV ON CTE_UNV.KID = tt_sp_r_denormalizeddata.KID ');

    -- Group by KID and TID
    SET @sql_stmt = CONCAT(@sql_stmt, 'GROUP BY KID, TID');

    -- Prepare and execute the dynamic SQL statement
    PREPARE stmt FROM @sql_stmt;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;

    -- Drop the temporary table
    DROP TEMPORARY TABLE IF EXISTS tt_sp_r_denormalizeddata;
END $$
DELIMITER ;
