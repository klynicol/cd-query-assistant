# Order Status or Milestone's

-- Example SQL Queries for Retrieving Order Status from the track table
joined with the mile table and the ordhdr table.

Combined this is what allows users of this application to see where the order is at in the facility.

-- ============================================================================
-- PATTERN 1: Get the latest order status for a specific order
-- This is the most common pattern used in the codebase
-- ============================================================================
SELECT 
    m.mileID,
    m.mileDesc,           -- Internal status description
    m.publicDesc,         -- Public-facing status description
    m.shortDesc,          -- Short status description
    t.lastDateTime,       -- When this status was set
    t.trackID
FROM track t 
LEFT JOIN mile m ON t.mileID = m.mileID
LEFT JOIN ordhdr oh ON oh.ordID = t.ordID
WHERE oh.ordNum = '12345'     -- Replace with your order number
ORDER BY t.lastDateTime DESC
LIMIT 1;

-- ============================================================================
-- PATTERN 2: Get order status using ordhdr.lastTrackID (most recent track entry)
-- This uses the lastTrackID field which points to the most recent track entry
-- ============================================================================
SELECT 
    oh.ordNum,
    oh.ordID,
    m.mileID,
    m.mileDesc,
    m.publicDesc AS orderStatus,
    m.shortDesc,
    t.lastDateTime AS statusDateTime
FROM ordhdr oh
LEFT JOIN track t ON t.trackID = oh.lastTrackID
LEFT JOIN mile m ON t.mileID = m.mileID
WHERE oh.ordNum = '12345';   -- Replace with your order number

-- ============================================================================
-- PATTERN 3: Get order status using subquery to find latest track entry
-- Useful when you need the status as a column in a larger query
-- ============================================================================
SELECT 
    oh.ordNum,
    oh.ordID,
    oh.shipDate,
    (SELECT m.shortDesc
     FROM track t
     LEFT JOIN mile m ON t.mileID = m.mileID
     WHERE t.ordID = oh.ordID
     ORDER BY m.seq DESC
     LIMIT 1) AS orderStatus
FROM ordhdr oh
WHERE oh.ordNum = '12345';   -- Replace with your order number

-- ============================================================================
-- PATTERN 4: Get order status for multiple orders
-- Useful for listing orders with their current status
-- ============================================================================
SELECT 
    oh.ordNum,
    oh.ordID,
    oh.shipDate,
    c.custName,
    m.mileDesc AS statusDescription,
    m.publicDesc AS publicStatus,
    m.shortDesc AS shortStatus,
    t.lastDateTime AS statusDateTime
FROM ordhdr oh
LEFT JOIN cust c ON c.custID = oh.custID
LEFT JOIN track t ON t.trackID = oh.lastTrackID
LEFT JOIN mile m ON t.mileID = m.mileID
WHERE oh.archive = 0
  AND oh.cancelled = 0
ORDER BY oh.shipDate ASC;

-- ============================================================================
-- PATTERN 5: Get all status history for an order (not just the latest)
-- Useful for tracking the progression of an order through different statuses
-- ============================================================================
SELECT 
    t.trackID,
    t.ordID,
    oh.ordNum,
    m.mileID,
    m.mileDesc,
    m.publicDesc,
    m.shortDesc,
    m.seq AS statusSequence,
    t.lastDateTime AS statusDateTime,
    t.startDateTime
FROM track t
LEFT JOIN mile m ON t.mileID = m.mileID
LEFT JOIN ordhdr oh ON oh.ordID = t.ordID
WHERE oh.ordNum = '12345'     -- Replace with your order number
ORDER BY t.lastDateTime DESC;

-- ============================================================================
-- PATTERN 6: Get order status with department information
-- Includes department details for production status tracking
-- ============================================================================
SELECT 
    oh.ordNum,
    d.deptDesc AS department,
    m.mileDesc AS statusDescription,
    m.shortDesc AS shortStatus,
    m.seq AS statusSequence,
    t.lastDateTime AS statusDateTime
FROM ordhdr oh
LEFT JOIN track t ON t.trackID = oh.lastTrackID
LEFT JOIN mile m ON t.mileID = m.mileID
LEFT JOIN dept d ON d.deptID = m.deptID
WHERE oh.ordNum = '12345';   -- Replace with your order number

-- ============================================================================
-- NOTES:
-- ============================================================================
-- - The 'track' table stores status changes/milestones for orders
-- - The 'mile' table contains the status definitions (mileID, descriptions, etc.)
-- - The 'ordhdr.lastTrackID' field points to the most recent track entry
-- - Use LEFT JOIN to handle orders that may not have any track entries yet
-- - Order by lastDateTime DESC or seq DESC to get the most recent status
-- - Common status fields from mile table:
--   * mileDesc: Internal description
--   * publicDesc: Public-facing description  
--   * shortDesc: Short abbreviation
--   * seq: Sequence number (higher = more recent status typically)

