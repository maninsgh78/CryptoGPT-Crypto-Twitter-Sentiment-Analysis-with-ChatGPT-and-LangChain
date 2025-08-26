import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import os

# --- Dashboard Configuration ---
st.set_page_config(
    page_title="Indian Stock Tracker",
    page_icon="📈",
    layout="wide"
)

# --- Data File Management ---
WISHLIST_FILE = "stock_wishlist.json"

def load_wishlist():
    if os.path.exists(WISHLIST_FILE):
        with open(WISHLIST_FILE, "r") as f:
            return json.load(f)
    return []

def save_wishlist(wishlist):
    with open(WISHLIST_FILE, "w") as f:
        json.dump(wishlist, f)

# --- Fetching Stock Data ---
@st.cache_data
def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        data = stock.history(period="1y")
        info = stock.info
        return data, info
    except Exception as e:
        st.error(f"Could not retrieve data for {symbol}. Please check the ticker symbol.")
        return None, None

# --- Main Dashboard Layout ---
st.title("Indian Stock Market Tracker")
st.markdown("A simple dashboard to track your favorite Indian stocks.")

# --- Wishlist Management ---
st.header("My Wishlist")
wishlist = load_wishlist()

with st.expander("Add a new stock"):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_symbol = st.text_input("Enter NSE Ticker Symbol (e.g., RELIANCE.NS)")
    with col2:
        new_target_price = st.number_input("Target Price (in INR)", min_value=0.0, format="%.2f")
    with col3:
        add_stock_button = st.button("Add to Wishlist")

    if add_stock_button and new_symbol:
        # Check if stock is already in the wishlist
        if any(item['symbol'] == new_symbol.upper() for item in wishlist):
            st.warning("This stock is already in your wishlist.")
        else:
            wishlist.append({
                "symbol": new_symbol.upper(),
                "target_price": new_target_price,
                "remarks": ""
            })
            save_wishlist(wishlist)
            st.success(f"Added {new_symbol.upper()} to your wishlist!")

# --- Display Wishlist Table ---
if wishlist:
    display_data = []
    for stock in wishlist:
        symbol = stock['symbol']
        data, info = get_stock_info(symbol)
        if data is not None and info is not None:
            current_price = info.get('currentPrice', 'N/A')
            day_change = info.get('regularMarketChangePercent', 'N/A')
            display_data.append({
                "Symbol": symbol,
                "Current Price": f"₹{current_price}",
                "Day Change %": f"{day_change:.2f}%" if isinstance(day_change, float) else "N/A",
                "Target Price": f"₹{stock['target_price']}",
                "Remarks": stock['remarks']
            })

    wishlist_df = pd.DataFrame(display_data)
    st.dataframe(wishlist_df, use_container_width=True, hide_index=True)

    # --- Interactive Chart and Remarks Section ---
    st.subheader("Stock Details")
    selected_symbol = st.selectbox("Select a stock to view details:", [item['symbol'] for item in wishlist])

    if selected_symbol:
        stock_data, stock_info = get_stock_info(selected_symbol)
        if stock_data is not None and stock_info is not None:
            current_remarks = next((item['remarks'] for item in wishlist if item['symbol'] == selected_symbol), "")
            current_target = next((item['target_price'] for item in wishlist if item['symbol'] == selected_symbol), 0.0)

            # --- Chart ---
            fig = go.Figure(data=[go.Candlestick(x=stock_data.index,
                                                open=stock_data['Open'],
                                                high=stock_data['High'],
                                                low=stock_data['Low'],
                                                close=stock_data['Close'])])
            fig.update_layout(title=f"1-Year Price Chart for {selected_symbol}",
                              xaxis_rangeslider_visible=False)
            fig.add_hline(y=current_target, annotation_text=f"Target Price: ₹{current_target}",
                          line_dash="dot", line_color="orange")
            st.plotly_chart(fig, use_container_width=True)
            
            # --- Remarks and Price Update ---
            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("Remarks")
                new_remarks = st.text_area(
                    "Why I added this stock:",
                    value=current_remarks,
                    height=200
                )
                if new_remarks != current_remarks:
                    for item in wishlist:
                        if item['symbol'] == selected_symbol:
                            item['remarks'] = new_remarks
                    save_wishlist(wishlist)
                    st.success("Remarks updated successfully!")

            with col2:
                st.subheader("Update Target Price")
                new_target = st.number_input(
                    "New Target Price",
                    min_value=0.0,
                    value=current_target,
                    key=f"target_{selected_symbol}",
                    format="%.2f"
                )
                update_button = st.button("Update Target Price")
                if update_button:
                    for item in wishlist:
                        if item['symbol'] == selected_symbol:
                            item['target_price'] = new_target
                    save_wishlist(wishlist)
                    st.success("Target price updated successfully!")

else:
    st.info("Your wishlist is empty. Add a stock using the input field above.")
