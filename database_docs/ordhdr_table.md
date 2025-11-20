# Order Header Table (ordhdr)

## Overview
The `ordhdr` table is the main order header table containing primary order information for the business system.

## Purpose
This table stores the core order data including order identification, customer information, order dates, status, and financial details.

## Key Fields
- **ordID**: Primary key for identifying orders
- **custID**: Links to customer information
- **ordDate**: When the order was placed

## Business Context
- Orders represent customer purchases and transactions
- Each order can have multiple line items (stored in related tables)
- Order status drives business processes and reporting
- Financial data is used for revenue analysis and reporting

## Common Query Patterns
- Find orders by date range
- Get orders by customer
- Analyze order status distribution
- Calculate total revenue by period
- Identify high-value orders

## Related Tables
- Links to customer tables for customer details
- Connects to order line item tables for detailed order contents
- References payment and shipping tables for fulfillment data

## Sample Queries
```sql
-- Recent orders
SELECT * FROM ordhdr WHERE ordDate >= CURDATE() - INTERVAL 30 DAY;

-- ============================================================================
-- Get order status using ordhdr.lastTrackID (most recent track entry)
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
WHERE oh.ordNum = 416328;   -- Replace with your order number / SWO (sales work order)

-- Top customers by order value
SELECT c.custName, c.custID, SUM(o.ordTotal) as total 
FROM ordhdr o
JOIN cust c
on c.custID = o.custID 
GROUP BY custID
ORDER BY SUM(o.ordTotal) DESC;
```
