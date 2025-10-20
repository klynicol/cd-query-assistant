# Common Query Examples

## Order Queries

### Recent Orders
```sql
-- Get orders from the last 30 days
SELECT * FROM ordhdr 
WHERE order_date >= CURDATE() - INTERVAL 30 DAY 
ORDER BY order_date DESC;
```

### Order Status Analysis
```sql
-- Count orders by status
SELECT status, COUNT(*) as order_count 
FROM ordhdr 
GROUP BY status 
ORDER BY order_count DESC;
```

### High-Value Orders
```sql
-- Orders over $1000
SELECT order_id, customer_id, order_date, total_amount 
FROM ordhdr 
WHERE total_amount > 1000 
ORDER BY total_amount DESC;
```

## Customer Analysis

### Top Customers by Revenue
```sql
-- Customer revenue summary
SELECT customer_id, 
       COUNT(*) as order_count,
       SUM(total_amount) as total_revenue,
       AVG(total_amount) as avg_order_value
FROM ordhdr 
GROUP BY customer_id 
ORDER BY total_revenue DESC 
LIMIT 10;
```

### Customer Order History
```sql
-- Orders for a specific customer
SELECT order_id, order_date, status, total_amount 
FROM ordhdr 
WHERE customer_id = ? 
ORDER BY order_date DESC;
```

## Time-Based Analysis

### Monthly Revenue
```sql
-- Revenue by month
SELECT 
    YEAR(order_date) as year,
    MONTH(order_date) as month,
    COUNT(*) as order_count,
    SUM(total_amount) as total_revenue
FROM ordhdr 
WHERE order_date >= CURDATE() - INTERVAL 12 MONTH
GROUP BY YEAR(order_date), MONTH(order_date)
ORDER BY year DESC, month DESC;
```

### Daily Order Volume
```sql
-- Orders per day for the last 30 days
SELECT 
    DATE(order_date) as order_day,
    COUNT(*) as order_count,
    SUM(total_amount) as daily_revenue
FROM ordhdr 
WHERE order_date >= CURDATE() - INTERVAL 30 DAY
GROUP BY DATE(order_date)
ORDER BY order_day DESC;
```

## Status and Workflow Queries

### Pending Orders
```sql
-- Orders that need attention
SELECT order_id, customer_id, order_date, total_amount 
FROM ordhdr 
WHERE status IN ('pending', 'processing') 
ORDER BY order_date ASC;
```

### Completed Orders This Month
```sql
-- Successfully completed orders this month
SELECT COUNT(*) as completed_orders, SUM(total_amount) as revenue 
FROM ordhdr 
WHERE status = 'completed' 
AND YEAR(order_date) = YEAR(CURDATE()) 
AND MONTH(order_date) = MONTH(CURDATE());
```

## Data Quality Queries

### Orders Missing Customer Information
```sql
-- Orders with invalid customer references
SELECT order_id, customer_id, order_date 
FROM ordhdr 
WHERE customer_id IS NULL OR customer_id = '';
```

### Orders with Zero Amount
```sql
-- Orders with no financial value
SELECT order_id, customer_id, order_date, total_amount 
FROM ordhdr 
WHERE total_amount = 0 OR total_amount IS NULL;
```
