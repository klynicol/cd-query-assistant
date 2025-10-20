# Database Table Relationships

## Overview
This document describes the relationships between tables in the ot_cdc database system.

## Primary Tables

### ordhdr (Order Header)
- **Primary Key**: order_id
- **Purpose**: Main order information and header data
- **Key Relationships**:
  - Links to customer tables via customer_id
  - Connects to order line item tables for detailed order contents
  - References payment tables for financial transactions
  - Links to shipping tables for fulfillment data

## Common Join Patterns

### Order Analysis
```sql
-- Orders with customer information
SELECT o.*, c.customer_name, c.email 
FROM ordhdr o 
JOIN customers c ON o.customer_id = c.customer_id;

-- Orders with line item details
SELECT o.order_id, o.order_date, ol.product_id, ol.quantity, ol.unit_price
FROM ordhdr o 
JOIN order_lines ol ON o.order_id = ol.order_id;
```

### Revenue Analysis
```sql
-- Revenue by customer
SELECT c.customer_name, SUM(o.total_amount) as total_revenue
FROM ordhdr o 
JOIN customers c ON o.customer_id = c.customer_id
GROUP BY c.customer_name
ORDER BY total_revenue DESC;
```

### Status Tracking
```sql
-- Order status with customer details
SELECT o.order_id, o.order_date, o.status, c.customer_name
FROM ordhdr o 
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'pending';
```

## Data Flow
1. **Order Creation**: New orders are created in ordhdr table
2. **Customer Linking**: Orders are linked to customers via customer_id
3. **Line Items**: Detailed order contents are stored in related line item tables
4. **Status Updates**: Order status changes are tracked in ordhdr
5. **Financial Processing**: Payment and billing data connects to ordhdr

## Business Rules
- Every order must have a valid customer_id
- Order status follows predefined workflow states
- Total amounts are calculated from line items
- Order dates are automatically set on creation
- Financial data is immutable once orders are completed

## Reporting Patterns
- **Customer Analysis**: Join ordhdr with customer tables
- **Product Analysis**: Join ordhdr with line items and product tables
- **Financial Reporting**: Aggregate ordhdr totals by various dimensions
- **Operational Reports**: Filter ordhdr by status and date ranges
