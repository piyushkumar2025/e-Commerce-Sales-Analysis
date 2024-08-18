#!/usr/bin/env python
# coding: utf-8

#   # Analyzed a Dataset of 100,000 orders spanning 2016-2018 using SQL and Python.

# In[1]:


import pandas as pd
import numpy as np
import mysql.connector
import os

# List of CSV files and their corresponding table names.

csv_files = [
    ('customers.csv', 'customers'),
    ('orders.csv', 'orders'),
    ('sellers.csv', 'sellers'),
    ('products.csv', 'products'),
    ('geolocation.csv', 'geolocation'),
    ('payments.csv', 'payments'),
    ('order_items.csv', 'order_items')
]


# Connect to the MySQL database
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='PIyush@12345',
    database='ecommerce'
)
cursor = conn.cursor()


# Folder containing the CSV files
folder_path ='D:\sql project\Ecommerce'

def get_sql_type(dtype):
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        return 'FLOAT'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BOOLEAN'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME'
    else:
        return 'TEXT'

for csv_file, table_name in csv_files:
    file_path = os.path.join(folder_path, csv_file)
    
    # Read the CSV file into a pandas DataFrame
    df = pd.read_csv(file_path)
    
    # Replace NaN with None to handle SQL NULL
    df = df.where(pd.notnull(df), None)
    
    # Debugging: Check for NaN values
    print(f"Processing {csv_file}")
    print(f"NaN values before replacement:\n{df.isnull().sum()}\n")

    # Clean column names
    df.columns = [col.replace(' ', '_').replace('-', '_').replace('.', '_') for col in df.columns]

    # Generate the CREATE TABLE statement with appropriate data types
    columns = ', '.join([f'`{col}` {get_sql_type(df[col].dtype)}' for col in df.columns])
    create_table_query = f'CREATE TABLE IF NOT EXISTS `{table_name}` ({columns})'
    cursor.execute(create_table_query)

    # Insert DataFrame data into the MySQL table
    for _, row in df.iterrows():
        # Convert row to tuple and handle NaN/None explicitly
        values = tuple(None if pd.isna(x) else x for x in row)
        sql = f"INSERT INTO `{table_name}` ({', '.join(['`' + col + '`' for col in df.columns])}) VALUES ({', '.join(['%s'] * len(row))})"
        cursor.execute(sql, values)

    # Commit the transaction for the current CSV file
    conn.commit()

# Close the connection
conn.close()


# In[2]:


import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector

conn=mysql.connector.connect(host="localhost",
                            username="root",
                            password="PIyush@12345",
                            database="ecommerce")

cur=conn.cursor()


# # 1. List all unique cities where customers are located.

# In[3]:


query="select distinct customer_city from customers"

cur.execute(query)
output=cur.fetchall()
output


# # 2. Count the number of orders placed in 2017.

# In[4]:


query="select count(order_id) from orders where year(order_purchase_timestamp)=2017"

cur.execute(query)
output=cur.fetchall()
orders=output[0][0]
print('total orders placed in 2017 is' ,orders)


# # 3. Find the total sales per category.

# In[5]:


query = """ select upper(products.product_category) category, 
round(sum(payments.payment_value),2) sales
from products join order_items 
on products.product_id = order_items.product_id
join payments 
on payments.order_id = order_items.order_id
group by category
"""

cur.execute(query)
output=cur.fetchall()
output


df = pd.DataFrame(output, columns = ["Category", "Sales"])
df


# # 4. Calculate the percentage of orders that were paid in installments.

# In[6]:


query = """ select ((sum(case when payment_installments >= 1 then 1
else 0 end))/count(*))*100 from payments
"""

cur.execute(query)

output = cur.fetchall()
data= output[0][0]

print("the percentage of orders that were paid in installments is", data)


# # 5. Count the number of customers from each state. 

# In[7]:


query = """ select customer_state ,count(customer_id)
from customers group by customer_state
"""

cur.execute(query)

output = cur.fetchall()
df = pd.DataFrame(output, columns = ["state", "customer_count" ])
df = df.sort_values(by = "customer_count", ascending= False)
plt.figure(figsize = (8,3))
plt.bar(df["state"], df["customer_count"])
plt.xticks(rotation = 90)
plt.xlabel("states")
plt.ylabel("customer_count")
plt.title("Count of Customers by States")
plt.show()


# # 6. Calculate the number of orders per month in 2018.

# In[8]:


query = """ select monthname(order_purchase_timestamp) months, count(order_id) order_count
from orders where year(order_purchase_timestamp) = 2018
group by months
"""

cur.execute(query)

data = cur.fetchall()
df = pd.DataFrame(data, columns = ["months", "order_count"])
months = ["January", "February","March","April","May","June","July","August","September","October"]

ax = sns.barplot(x = df["months"],y =  df["order_count"], data = df, order = months, color = "blue")
plt.xticks(rotation = 45)
ax.bar_label(ax.containers[0])
plt.title("Count of Orders by Months is 2018")

plt.show()


# # 7. Find the average number of products per order, grouped by customer city.

# In[9]:


query = """with count_per_order as 
(select orders.order_id, orders.customer_id, count(order_items.order_id) as oc
from orders join order_items
on orders.order_id = order_items.order_id
group by orders.order_id, orders.customer_id)

select customers.customer_city, round(avg(count_per_order.oc),2) average_orders
from customers join count_per_order
on customers.customer_id = count_per_order.customer_id
group by customers.customer_city order by average_orders desc
"""

cur.execute(query)

output = cur.fetchall()
df = pd.DataFrame(output,columns = ["customer city", "average products/order"])
df.head(10)


# # 8. Calculate the percentage of total revenue contributed by each product category.

# In[11]:


query = """select upper(products.product_category) category, 
round((sum(payments.payment_value)/(select sum(payment_value) from payments))*100,2) sales_percentage
from products join order_items 
on products.product_id = order_items.product_id
join payments 
on payments.order_id = order_items.order_id
group by category order by sales_percentage desc"""


cur.execute(query)
output = cur.fetchall()
df = pd.DataFrame(output,columns = ["Category", "percentage distribution"])
df.head()


# # 9.Identify the correlation between product price and the number of times a product has been purchased.

# In[24]:


import pandas as pd
import numpy as np
import mysql.connector
import os
import matplotlib.pyplot as plt
import seaborn as sns


# In[26]:


conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='PIyush@12345',
    database='ecommerce'
)
cur = conn.cursor()


# In[28]:


query = """select products.product_category, 
count(order_items.product_id),
round(avg(order_items.price),2)
from products join order_items
on products.product_id = order_items.product_id
group by products.product_category"""

cur.execute(query)
output=cur.fetchall()
df = pd.DataFrame(output,columns = ["Category", "order_count","price"])

arr1 = df["order_count"]
arr2 = df["price"]

a = np.corrcoef([arr1,arr2])
print("the correlation is", a[0][-1])


# # 10.Calculate the total revenue generated by each seller, and rank them by revenue.

# In[32]:


query = """ select *, dense_rank() over(order by revenue desc) as rn from
(select order_items.seller_id, sum(payments.payment_value)
revenue from order_items join payments
on order_items.order_id = payments.order_id
group by order_items.seller_id) as a """

cur.execute(query)
output = cur.fetchall()
df = pd.DataFrame(output, columns = ["seller_id", "revenue", "rank"])
df = df.head()
sns.barplot(x = "seller_id", y = "revenue", data = df)
plt.xticks(rotation = 80)
plt.show()


# # 11.Calculate the moving average of order values for each customer over their order history.

# In[34]:


query = """select years, months , payment, sum(payment)
over(order by years, months) cumulative_sales from 
(select year(orders.order_purchase_timestamp) as years,
month(orders.order_purchase_timestamp) as months,
round(sum(payments.payment_value),2) as payment from orders join payments
on orders.order_id = payments.order_id
group by years, months order by years, months) as a
"""
cur.execute(query)
output = cur.fetchall()
df = pd.DataFrame(output)
df


# # 12.Calculate the cumulative sales per month for each year.

# In[36]:


query = """select years, months , payment, sum(payment)
over(order by years, months) cumulative_sales from 
(select year(orders.order_purchase_timestamp) as years,
month(orders.order_purchase_timestamp) as months,
round(sum(payments.payment_value),2) as payment from orders join payments
on orders.order_id = payments.order_id
group by years, months order by years, months) as a
"""
cur.execute(query)
output = cur.fetchall()
df = pd.DataFrame(output)
df


# # 13.Calculate the year-over-year growth rate of total sales.

# In[39]:


query = """with a as(select year(orders.order_purchase_timestamp) as years,
round(sum(payments.payment_value),2) as payment from orders join payments
on orders.order_id = payments.order_id
group by years order by years)

select years, ((payment - lag(payment, 1) over(order by years))/
lag(payment, 1) over(order by years)) * 100 from a"""

cur.execute(query)
output = cur.fetchall()
df = pd.DataFrame(output, columns = ["years", "yoy % growth"])
df


# # 14.Calculate the retention rate of customers, defined as the percentage of customers who make another purchase within 6 months of their first purchase.

# In[40]:


query = """with a as (select customers.customer_id,
min(orders.order_purchase_timestamp) first_order
from customers join orders
on customers.customer_id = orders.customer_id
group by customers.customer_id),

b as (select a.customer_id, count(distinct orders.order_purchase_timestamp) next_order
from a join orders
on orders.customer_id = a.customer_id
and orders.order_purchase_timestamp > first_order
and orders.order_purchase_timestamp < 
date_add(first_order, interval 6 month)
group by a.customer_id) 

select 100 * (count( distinct a.customer_id)/ count(distinct b.customer_id)) 
from a left join b 
on a.customer_id = b.customer_id ;"""

cur.execute(query)
output = cur.fetchall()

output


# # 15.Identify the top 3 customers who spent the most money in each year.

# In[44]:


query = """select years, customer_id, payment, d_rank
from
(select year(orders.order_purchase_timestamp) years,
orders.customer_id,
sum(payments.payment_value) payment,
dense_rank() over(partition by year(orders.order_purchase_timestamp)
order by sum(payments.payment_value) desc) d_rank
from orders join payments 
on payments.order_id = orders.order_id
group by year(orders.order_purchase_timestamp),
orders.customer_id) as a
where d_rank <= 3 ;"""

cur.execute(query)
data = cur.fetchall()
df = pd.DataFrame(data, columns = ["years","id","payment","rank"])
sns.barplot(x = "id", y = "payment", data = df, hue = "years")
plt.xticks(rotation = 90)
plt.show()

