# Order Header Table (ordhdr)

## Overview
The `ordhdr` table is the main order header table containing primary order information for the business system.

## Purpose
This table stores the core order data including order identification, customer information, order dates, status, and financial details.

## Key Fields
- **Order ID**: Primary key for identifying orders
- **Customer ID**: Links to customer information
- **Order Date**: When the order was placed
- **Order Status**: Current status of the order (pending, completed, cancelled, etc.)
- **Total Amount**: Total value of the order
- **Created Date**: When the order record was created
- **Updated Date**: When the order was last modified

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
SELECT * FROM ordhdr WHERE order_date >= CURDATE() - INTERVAL 30 DAY;

-- Orders by status
SELECT status, COUNT(*) as count FROM ordhdr GROUP BY status;

-- Top customers by order value
SELECT customer_id, SUM(total_amount) as total 
FROM ordhdr 
GROUP BY customer_id 
ORDER BY total DESC;
```
