
import streamlit as st
import pandas as pd
import urllib.parse
from pathlib import Path

# File paths
products_file = Path("products.xlsx")
customers_file = Path("customers.xlsx")

# Load or initialize products
if products_file.exists():
    products_df = pd.read_excel(products_file)
else:
    products_df = pd.DataFrame(columns=["Product", "Price", "Stock"])

st.title("The Artsy Retreat - Invoice & Stock Manager")

# ---- Admin Section ----
st.header("Admin: Add/Edit Products")
with st.form("product_form"):
    new_product = st.text_input("Product Name")
    new_price = st.number_input("Price", min_value=0.0)
    new_stock = st.number_input("Stock Quantity", min_value=0)
    submitted = st.form_submit_button("Add/Update Product")
    if submitted and new_product:
        if new_product in products_df["Product"].values:
            # Update existing product
            products_df.loc[products_df["Product"] == new_product, ["Price", "Stock"]] = [new_price, new_stock]
        else:
            products_df = pd.concat([products_df, pd.DataFrame([[new_product, new_price, new_stock]], columns=["Product", "Price", "Stock"])])
        products_df.to_excel(products_file, index=False)
        st.success(f"Product {new_product} added/updated successfully!")

st.dataframe(products_df)

# ---- Customer Invoice Section ----
st.header("Create Customer Invoice")

customer_name = st.text_input("Customer Name")
customer_mobile = st.text_input("Mobile Number (with country code, e.g., 919876543210)")

# Filter products with stock > 0
available_products = products_df[products_df["Stock"] > 0]

if available_products.empty:
    st.warning("No products available in stock.")
else:
    selected_products = st.multiselect("Select Products", available_products["Product"].tolist())
    quantities = {}
    total_amount = 0
    invoice_lines = []

    for prod in selected_products:
        max_stock = int(products_df.loc[products_df["Product"] == prod, "Stock"].values[0])
        qty = st.number_input(f"Quantity for {prod} (max {max_stock})", min_value=1, max_value=max_stock, value=1, key=prod)
        price = products_df.loc[products_df["Product"] == prod, "Price"].values[0]
        total = qty * price
        quantities[prod] = qty
        total_amount += total
        invoice_lines.append(f"{prod} x {qty} (${price})")

    if st.button("Generate Invoice & WhatsApp Link") and customer_name and customer_mobile and selected_products:
        # Update stock
        for prod, qty in quantities.items():
            products_df.loc[products_df["Product"] == prod, "Stock"] -= qty
        products_df.to_excel(products_file, index=False)

        # Save customer invoice
        if customers_file.exists():
            customers_df = pd.read_excel(customers_file)
        else:
            customers_df = pd.DataFrame(columns=["Name", "Mobile", "Products", "Total"])
        customers_df = pd.concat([customers_df, pd.DataFrame([[customer_name, customer_mobile, ", ".join(invoice_lines), total_amount]], columns=customers_df.columns)])
        customers_df.to_excel(customers_file, index=False)

        st.success(f"Invoice saved! Total: ${total_amount}")

        # WhatsApp link
        message = f"Hello {customer_name}, thank you for buying from The Artsy Retreat! Your invoice:\n" + "\n".join(invoice_lines) + f"\nTotal: ${total_amount}\n. We are happy to inform you that we do conduct workshops. If interested please ping us back!"
        encoded_msg = urllib.parse.quote(message)
        wa_link = f"https://wa.me/{customer_mobile}?text={encoded_msg}"
        
        st.markdown(f"[Send Invoice on WhatsApp]({wa_link})", unsafe_allow_html=True)

    
