import streamlit as st
import pandas as pd
import urllib.parse
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- Custom Background & Styles ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #FFDEE9 0%, #B5FFFC 100%);
        background-attachment: fixed;
    }
    .stApp h1, .stApp h2, .stApp h3 {
        font-family: 'Comic Sans MS', cursive, sans-serif;
        color: #333333;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Optional header image
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1f/Paint_brush_icon.svg/1200px-Paint_brush_icon.svg.png", width=80)
st.title("🎨 The Artsy Retreat - Invoice & Stock Manager")

# --- Google Sheets Setup ---
SHEET_NAME = "Artsy Retreat Data"
SERVICE_ACCOUNT_FILE = "service_account.json"

scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
client = gspread.authorize(creds)

# Open sheets
products_sheet = client.open(SHEET_NAME).worksheet("Products")
try:
    invoices_sheet = client.open(SHEET_NAME).worksheet("Invoices")
except gspread.exceptions.WorksheetNotFound:
    invoices_sheet = client.open(SHEET_NAME).add_worksheet(title="Invoices", rows=100, cols=10)

# Load products into DataFrame
products_df = pd.DataFrame(products_sheet.get_all_records())

# --- INVOICE SECTION ---
st.header("🧾 Create Customer Invoice")

customer_name = st.text_input("Customer Name")
customer_mobile = st.text_input("Mobile Number (with country code, e.g., 919876543210)")

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
            row_idx = products_df.index[products_df["Product"] == prod][0] + 2  # +2 for header
            new_stock = products_df.loc[products_df["Product"] == prod, "Stock"].values[0] - qty
            products_sheet.update_cell(row_idx, 3, new_stock)  # column 3 = Stock

        # Save invoice
        invoice_row = [customer_name, customer_mobile, ", ".join(invoice_lines), total_amount]
        invoices_sheet.append_row(invoice_row)

        st.success(f"Invoice saved! Total: ${total_amount}")

        # WhatsApp link
        message = f"Hello {customer_name}, thank you for buying from The Artsy Retreat! Your invoice:\n" + "\n".join(invoice_lines) + f"\nTotal: ${total_amount}\nWe also conduct workshops!"
        encoded_msg = urllib.parse.quote(message)
        wa_link = f"https://wa.me/{customer_mobile}?text={encoded_msg}"

        st.markdown(f"[Send Invoice on WhatsApp]({wa_link})", unsafe_allow_html=True)

# --- STOCK SECTION ---
st.header("📦 Current Products & Stock")
# Reload products from sheet to show live updated stock
products_df = pd.DataFrame(products_sheet.get_all_records())
st.dataframe(products_df)
