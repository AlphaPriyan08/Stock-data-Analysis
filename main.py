import time
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import datetime

# Set page configuration
st.set_page_config(page_title="Interactive Stock Dashboard", layout="wide")
st.title("Interactive Stock Comparison Dashboard")

# Auto-refresh: define refresh interval in seconds (e.g., refresh every 60 seconds)
REFRESH_INTERVAL = 60

# Initialize session state countdown for auto-refresh
if "countdown" not in st.session_state:
    st.session_state.countdown = REFRESH_INTERVAL

# Auto-refresh mechanism
if st.session_state.countdown <= 0:
    st.experimental_rerun()
else:
    st.info(f"Page will auto-refresh in {st.session_state.countdown} seconds.")
    time.sleep(1)
    st.session_state.countdown -= 1

# Sidebar: User Inputs
st.sidebar.header("User Inputs")
default_tickers = ["SBIN.NS", "HDFC.NS", "ICICIBANK.NS", "AXISBANK.NS", "KOTAKBANK.NS"]
selected_tickers = st.sidebar.multiselect("Select Stocks:", options=default_tickers, default=default_tickers)
today = datetime.date.today()
start_date = st.sidebar.date_input("Start Date", value=today - datetime.timedelta(days=5*365))
end_date = st.sidebar.date_input("End Date", value=today)
if start_date > end_date:
    st.sidebar.error("Error: Start date must be before end date.")

# Function to fetch stock data
@st.cache_data
def fetch_stock_data(ticker, start_date, end_date):
    try:
        data = yf.download(ticker, start=start_date, end=end_date)
        if data.empty:
            st.warning(f"No data found for {ticker}. This stock will be excluded from the analysis.")
            return None
        else:
            data.reset_index(inplace=True)
            data['Ticker'] = ticker
            return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker}: {e}")
        return None

# Fetch data for each selected ticker
data_dict = {}
valid_tickers = []
if selected_tickers and start_date <= end_date:
    st.write("Fetching data for selected tickers...")
    for ticker in selected_tickers:
        data = fetch_stock_data(ticker, start_date, end_date)
        if data is not None:
            data_dict[ticker] = data
            valid_tickers.append(ticker)

    if not valid_tickers:
        st.error("No valid data found for any of the selected tickers. Please try different stocks or date range.")
    else:
        st.success(f"Data fetched successfully for: {', '.join(valid_tickers)}")

# Combine all data into a single DataFrame
if valid_tickers:
    df_all = pd.concat(data_dict.values(), ignore_index=True)

    # Flatten multi-level columns if they exist
    if isinstance(df_all.columns, pd.MultiIndex):
        df_all.columns = ['_'.join(col).strip() if isinstance(col, tuple) else col for col in df_all.columns]

    # Optionally display raw data
    if st.checkbox("Show Raw Data"):
        st.write(df_all)

    # 1. Interactive Line Chart for Closing Prices
    st.header("Closing Prices Over Time")

    fig_line = px.line(df_all, x='Date', y='Close', color='Ticker', title="Historical Closing Prices")
    fig_line.update_layout(yaxis_title="Closing Price")
    st.plotly_chart(fig_line, use_container_width=True)

    # 2. Boxplot of Closing Prices
    st.header("Boxplot of Closing Prices")
    fig_box = px.box(df_all, x='Ticker', y='Close', title="Distribution of Closing Prices")
    st.plotly_chart(fig_box, use_container_width=True)

    # 3. Histogram of Daily Returns
    st.header("Histogram of Daily Returns")
    df_all['Daily Return'] = df_all.groupby('Ticker')['Close'].pct_change()
    fig_hist = px.histogram(df_all, x="Daily Return", color='Ticker', barmode="overlay", nbins=50, title="Histogram of Daily Returns")
    st.plotly_chart(fig_hist, use_container_width=True)

    # 4. Scatter Plot to Compare Two Stocks with Regression Line
    if len(valid_tickers) >= 2:
        st.header("Compare Two Stocks")
        ticker1 = st.selectbox("Select First Stock", options=valid_tickers, index=0)
        ticker2 = st.selectbox("Select Second Stock", options=valid_tickers, index=1)
        if ticker1 == ticker2:
            st.warning("Please select two different stocks to compare.")
        else:
            df_compare = df_all[df_all['Ticker'].isin([ticker1, ticker2])].pivot(index='Date', columns='Ticker', values='Close').dropna().reset_index()
            if ticker1 in df_compare.columns and ticker2 in df_compare.columns:
                fig_scatter = px.scatter(df_compare, x=ticker1, y=ticker2, trendline="ols", title=f"Scatter Plot: {ticker1} vs {ticker2}")
                fig_scatter.update_layout(
                    xaxis_title=f"{ticker1} Closing Price",
                    yaxis_title=f"{ticker2} Closing Price",
                    legend_title_text="Trendline"
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.error(f"Data for {ticker1} or {ticker2} is missing.")
else:
    st.info("Please select at least one stock and ensure the date range is valid.")
