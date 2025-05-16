import streamlit as st
import pandas as pd
import plotly.express as px
import openai

# --- Streamlit Page Setup ---
st.set_page_config(page_title="Spending Tracker", layout="centered")
st.title("💳 Personal Spending Dashboard")
st.write("Upload a CSV of your transactions to view your spending habits.")

# --- File Upload ---
uploaded_file = st.file_uploader("Upload your CSV or PDF file", type=["csv", "pdf"])

# --- OpenAI API Setup ---
openai_api_key = st.text_input("Enter your OpenAI API Key", type="password")
use_ai = st.checkbox("Use AI-based Categorization")

# --- AI Categorization Function ---
def ai_categorize(description, api_key):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that classifies financial transactions into categories like 'Groceries', 'Entertainment', 'Shopping', 'Income', 'Utilities', 'Transport', or 'Other'."},
                {"role": "user", "content": f"Categorize this transaction: {description}"}
            ],
            api_key=api_key
        )
        category = response['choices'][0]['message']['content'].strip()
        return category
    except Exception as e:
        return "Other"

# --- Rule-based Categorization Function ---
def rule_based_categorize(desc):
    desc = str(desc).lower()
    if "netflix" in desc:
        return "Entertainment"
    elif "amazon" in desc:
        return "Shopping"
    elif "costco" in desc or "grocery" in desc:
        return "Groceries"
    elif "payroll" in desc or "income" in desc:
        return "Income"
    return "Other"

# --- Process Uploaded File ---
from io import StringIO
import pdfplumber
if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".pdf"):
                with pdfplumber.open(uploaded_file) as pdf:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                df = pd.read_csv(StringIO(text), encoding_errors='ignore')
            else:
                df = pd.read_csv(uploaded_file)

        # Basic structure check
        required_columns = {"Date", "Description", "Amount"}
        if not required_columns.issubset(df.columns):
            st.error("CSV must include 'Date', 'Description', and 'Amount' columns.")
        else:
            # Categorize transactions
            if use_ai and openai_api_key:
                with st.spinner("Categorizing with AI..."):
                    df["Category"] = df["Description"].apply(lambda x: ai_categorize(x, openai_api_key))
            else:
                df["Category"] = df["Description"].apply(rule_based_categorize)

            # Show checkbox to view raw data
            if st.checkbox("Show Raw Data"):
                st.dataframe(df)

            # Filter for expenses
            expense_df = df[df["Amount"] < 0].copy()
            expense_df["Amount"] = expense_df["Amount"].abs()

            # Group and plot
            category_summary = expense_df.groupby("Category")["Amount"].sum().reset_index()

            st.subheader("📊 Spending by Category")
            fig = px.pie(category_summary, names="Category", values="Amount", title="Spending by Category")
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload a CSV file to get started.")
