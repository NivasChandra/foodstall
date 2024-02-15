import sqlite3
import streamlit as st
import pandas as pd

def init_db():
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, stall_id INTEGER, name TEXT, price REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS transactions
                 (id INTEGER PRIMARY KEY, stall_id INTEGER, product_id INTEGER, quantity INTEGER, customer_name TEXT, date_time TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_product(stall_id, name, price):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("INSERT INTO products (stall_id, name, price) VALUES (?, ?, ?)", (stall_id, name, price))
    conn.commit()
    conn.close()

def add_transaction(stall_id, product_id, quantity, customer_name):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    from datetime import datetime
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO transactions (stall_id, product_id, quantity, customer_name, date_time) VALUES (?, ?, ?, ?, ?)",
              (stall_id, product_id, quantity, customer_name, now))
    conn.commit()
    conn.close()

def get_products(stall_id):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("SELECT id, name, price FROM products WHERE stall_id=?", (stall_id,))
    products = c.fetchall()
    conn.close()
    return products

def get_product_price(product_id):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("SELECT price FROM products WHERE id=?", (product_id,))
    price = c.fetchone()[0]
    conn.close()
    return price

def get_selected_product_details(selected_products):
    product_details = []
    total_price = 0
    for product_id, quantity in selected_products:
        price = get_product_price(product_id)
        total_price += price * quantity
        product_details.append({'Product ID': product_id, 'Name': get_product_name(product_id), 'Quantity': quantity, 'Price': price})
    return product_details, total_price

def get_product_name(product_id):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("SELECT name FROM products WHERE id=?", (product_id,))
    name = c.fetchone()[0]
    conn.close()
    return name

def update_transaction(stall_id, product_id, quantity, customer_name):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("UPDATE transactions SET quantity = ? WHERE stall_id = ? AND product_id = ? AND customer_name = ?",
              (quantity, stall_id, product_id, customer_name))
    conn.commit()
    conn.close()

def delete_transaction(stall_id, product_id, customer_name):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute("DELETE FROM transactions WHERE stall_id = ? AND product_id = ? AND customer_name = ?",
              (stall_id, product_id, customer_name))
    conn.commit()
    conn.close()

st.title('Food Stall Management System')

# Stall selection
stall_id = st.selectbox('Select Stall', (1, 2))

tab2, tab3 = st.columns(2)

with st.sidebar:
    st.header('Add Product')
    stall_id_product = st.selectbox('Select Stall', (1, 2), key='stall_select_product')
    product_name = st.text_input('Product Name', key='product_name')
    product_price = st.number_input('Product Price', min_value=0.01, step=0.01, key='product_price')
    if st.button('Add Product', key='add_product'):
        add_product(stall_id_product, product_name, product_price)
        st.success('Product added successfully!')
        st.experimental_rerun()

with tab2:
    st.header('Create Bill')
    stall_id_bill = st.selectbox('Select Stall for Billing', (1, 2), key='stall_select_bill')
    
    product_options = get_products(stall_id_bill)
    product_dict = {product[0]: (product[1], product[2]) for product in product_options}
    
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    selected_product_id = st.selectbox('Select Product', options=list(product_dict.keys()), format_func=lambda x: product_dict[x][0], key='product_select')
    quantity = st.number_input('Quantity', min_value=1, value=1, key='quantity')
    if st.button('Add Product to Bill'):
        exists = False
        for idx, (product_id, _) in enumerate(st.session_state.selected_products):
            if product_id == selected_product_id:
                exists = True
                st.session_state.selected_products[idx] = (product_id, st.session_state.selected_products[idx][1] + quantity)
                break
        if not exists:
            st.session_state.selected_products.append((selected_product_id, quantity))
        st.success(f'Added {quantity} x {product_dict[selected_product_id][0]} to the bill.')
        st.experimental_rerun()

    customer_name = st.text_input('Customer Name', key='customer_name')
    
    if st.button('Generate Bill'):
        for product_id, quantity in st.session_state.selected_products:
            add_transaction(stall_id_bill, product_id, quantity, customer_name)
        st.markdown("<h2 style='color: green;'>✓ Bill Generated Successfully</h2>", unsafe_allow_html=True)
        st.session_state.selected_products = []
        st.experimental_rerun()

with tab3:
    st.header('Edit Bill')
    stall_id_edit = st.selectbox('Select Stall for Editing', (1, 2), key='stall_select_edit')
    
    customer_name_edit = st.text_input('Customer Name', key='customer_name_edit')
    
    if st.session_state.selected_products:
        product_details, total_price = get_selected_product_details(st.session_state.selected_products)
        df = pd.DataFrame(product_details)
        st.dataframe(df)
        st.write(f"**Total Cost:** ${total_price:.2f}")
        st.write("To edit the bill, enter the new quantity or click delete.")
        for idx, (product_id, _) in enumerate(st.session_state.selected_products):
            new_quantity = st.number_input(f'New Quantity for {product_dict[product_id][0]}', min_value=0, value=st.session_state.selected_products[idx][1])
            if new_quantity != st.session_state.selected_products[idx][1]:
                if new_quantity == 0:
                    delete_transaction(stall_id_edit, product_id, customer_name_edit)
                    del st.session_state.selected_products[idx]
                else:
                    update_transaction(stall_id_edit, product_id, new_quantity, customer_name_edit)
                    st.session_state.selected_products[idx] = (product_id, new_quantity)
        st.experimental_rerun()
    else:
        st.write("No products added to the bill yet.")



def get_sales_report(stall_id):
    conn = sqlite3.connect('food_stalls.db')
    c = conn.cursor()
    c.execute('''SELECT p.name, SUM(t.quantity), SUM(t.quantity * p.price)
                 FROM transactions t
                 JOIN products p ON t.product_id = p.id
                 WHERE t.stall_id=?
                 GROUP BY p.name''', (stall_id,))
    report = c.fetchall()
    conn.close()
    return report


st.header('Admin Overview')
admin_stall_id = st.selectbox('Select Stall for Overview', (1, 2), key='admin_stall')




# Display sales report for the selected stall
if st.button('Show Detailed Report', key='admin'):
    detailed_report = get_sales_report(admin_stall_id)
    detailed_df = pd.DataFrame(detailed_report, columns=['Product Name', 'Quantity Sold', 'Total Sales'])
    st.write(detailed_df)
