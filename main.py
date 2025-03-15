import time
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Set page configuration
st.set_page_config(page_title="Stock Dashboard", layout="wide")
st.title("Stock Comparison Dashboard")

# Auto-refresh: define refresh interval in seconds
REFRESH_INTERVAL = 60

# Initialize session state countdown for auto-refresh
if "countdown" not in st.session_state:
    st.session_state.countdown = REFRESH_INTERVAL

# Auto-refresh mechanism
if st.session_state.countdown <= 0:
    st.experimental_rerun()
else:
    # st.info(f"Page will auto-refresh in {st.session_state.countdown} seconds.")
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
            # Reset index to make Date a column
            data = data.reset_index()
            # Ensure column names are properly formatted
            data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
            # Add ticker column
            data['Ticker'] = ticker
            return data
    except Exception as e:
        st.error(f"An error occurred while fetching data for {ticker}: {e}")
        return None

# Main data processing
if selected_tickers and start_date <= end_date:
    # st.write("Fetching data for selected tickers...")

    # Store data for each ticker separately
    all_data = {}
    valid_tickers = []

    for ticker in selected_tickers:
        df = fetch_stock_data(ticker, start_date, end_date)
        if df is not None and not df.empty:
            all_data[ticker] = df.copy()
            valid_tickers.append(ticker)

    if not valid_tickers:
        st.error("No valid data found for any of the selected tickers. Please try different stocks or date range.")
    else:
        st.success(f"Data fetched successfully for: {', '.join(valid_tickers)}")

        # 1. Line chart for closing prices
        st.header("Closing Prices Over Time")

        # Create a proper dataframe for line chart
        line_chart_data = []
        for ticker in valid_tickers:
            df = all_data[ticker].copy()
            df = df[['Date', 'Close', 'Ticker']]
            line_chart_data.append(df)

        line_df = pd.concat(line_chart_data, ignore_index=True)

        # Debugging option
        if st.checkbox("Show DataFrame Info"):
            st.write("Line Chart DataFrame Columns:", line_df.columns.tolist())
            st.write("Sample Data:", line_df.head())

        try:
            fig = px.line(line_df, x='Date', y='Close', color='Ticker', title='Historical Closing Prices')
            fig.update_layout(yaxis_title="Closing Price")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating line chart: {e}")
            # Try an alternative approach with Plotly Graph Objects
            try:
                st.write("Attempting alternative plotting method...")
                fig = go.Figure()
                for ticker in valid_tickers:
                    ticker_data = line_df[line_df['Ticker'] == ticker]
                    fig.add_trace(go.Scatter(
                        x=ticker_data['Date'],
                        y=ticker_data['Close'],
                        mode='lines',
                        name=ticker
                    ))
                fig.update_layout(title='Historical Closing Prices',
                                 xaxis_title='Date',
                                 yaxis_title='Closing Price')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e2:
                st.error(f"Alternative plotting method also failed: {e2}")

        # 2. Box Plot
        st.header("Boxplot of Closing Prices")

        # Create a proper dataframe for boxplot
        box_plot_data = line_df.copy()  # We can reuse the line chart data

        try:
            fig = px.box(box_plot_data, x='Ticker', y='Close', title="Distribution of Closing Prices")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error creating boxplot: {e}")
            try:
                # Alternative approach using Plotly Graph Objects
                fig = go.Figure()
                for ticker in valid_tickers:
                    ticker_data = box_plot_data[box_plot_data['Ticker'] == ticker]
                    fig.add_trace(go.Box(
                        y=ticker_data['Close'],
                        name=ticker
                    ))
                fig.update_layout(title='Distribution of Closing Prices',
                                 yaxis_title='Close Price')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e2:
                st.error(f"Alternative boxplot method also failed: {e2}")

        # 3. Histogram of Daily Returns
        st.header("Histogram of Daily Returns")

        # Calculate daily returns ticker by ticker
        returns_data = []
        for ticker in valid_tickers:
            ticker_df = all_data[ticker].copy()
            ticker_df['Daily Return'] = ticker_df['Close'].pct_change()
            # Drop the first row with NaN
            ticker_df = ticker_df.dropna()
            returns_data.append(ticker_df[['Date', 'Daily Return', 'Ticker']])

        if returns_data:
            returns_df = pd.concat(returns_data, ignore_index=True)

            try:
                fig = px.histogram(returns_df, x='Daily Return', color='Ticker',
                                  barmode='overlay', nbins=50,
                                  title='Histogram of Daily Returns')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating histogram: {e}")
                try:
                    fig = go.Figure()
                    for ticker in valid_tickers:
                        ticker_data = returns_df[returns_df['Ticker'] == ticker]
                        fig.add_trace(go.Histogram(
                            x=ticker_data['Daily Return'],
                            name=ticker,
                            opacity=0.6
                        ))
                    fig.update_layout(title='Histogram of Daily Returns',
                                     xaxis_title='Daily Return',
                                     yaxis_title='Frequency',
                                     barmode='overlay')
                    st.plotly_chart(fig, use_container_width=True)
                except Exception as e2:
                    st.error(f"Alternative histogram method also failed: {e2}")

                else:
                    st.error(f"No overlapping dates found for {ticker1} and {ticker2}.")
else:
    st.info("Please select at least one stock and ensure the date range is valid.")