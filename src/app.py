import streamlit as st
import dotenv
import plotly.graph_objs as go
import pandas as pd
import numpy as np
from utils.helper import convert_timestamp_to_datetime
from datetime import timedelta, time
from utils.configure import load_config
from stream.storage.data_location import DataLocation
from order_book.order_book_history import MarketOrderBookHistory

# Load environment variables from .env file
dotenv.load_dotenv()
_, config = load_config()
data_location = DataLocation(config["paths"]["data_dir"], [])
events = data_location.load_json_data(file_name="eventLog.json")


@st.cache
def get_event_info(event_id):
    event_info = data_location.load_event(event_id)
    return event_info["event"], event_info["markets"]


@st.cache
def get_orderbook_data(event_id, market_id):
    orderbook_data = data_location.load_market(event_id, market_id)
    return orderbook_data


event_market_mapping = {}
st.sidebar.header('Select Event/Market')
event_id = st.sidebar.selectbox("Events", list(events), format_func=lambda x: events[x])

event, markets = get_event_info(event_id)
market_idx = st.sidebar.selectbox("Markets", list(range(len(markets))), format_func=lambda x: markets[x]['marketName'])
max_load_limit = st.sidebar.number_input("Max Load Limit", 0, 100000, 10000)

st.title(f'{events[event_id]}')
st.write("""
View game metrics over time, and compare between runners
""")


# TODO: Load game data for each runner
# TODO: Add loading indicator
# TODO: Add time slider
# TODO: Add start time and end time filter


@st.cache
def get_order_book_history(runner_ids, max_load_limit) -> MarketOrderBookHistory:
    market_history = MarketOrderBookHistory(runner_ids)
    market_id = markets[market_idx]['marketId']
    market_data = data_location.load_market(event_id, market_id)["mcm"]
    counter = 0

    for timestamp, packet in market_data.items():
        market_history.update(timestamp, packet)

        counter += 1
        if counter > max_load_limit:
            print(f"Reached Limit: Processed {len(market_history)} packets")
            break
    return market_history


def get_runner_data(runner_id, order_book_history):
    runner_history = order_book_history.get_runner_order_book(runner_id)
    game_start_time = convert_timestamp_to_datetime(runner_history.timestamps[0]).time()
    game_end_time = convert_timestamp_to_datetime(runner_history.timestamps[-1]).time()
    runner_timestamps = pd.to_datetime(runner_history.timestamps, unit='ms')

    data = pd.DataFrame({"Volume": runner_history.delta_tv_history,
                         "ATL Price": runner_history.atl_price_history,
                         "ATL Volume": runner_history.atl_volume_history,
                         "ATB Price": runner_history.atb_price_history,
                         "ATB Volume": runner_history.atb_volume_history,
                         "Close": runner_history.ltp_history,
                         "Total Volume": runner_history.tv_history},
                        index=runner_timestamps)
    return data, game_start_time, game_end_time


runners = markets[market_idx]['runners']
runner_tabs = st.tabs([runner['runnerName'] for runner in runners])
runner_ids = [runner['selectionId'] for runner in runners]

with st.spinner("Building Order Book History..."):
    order_book_history = get_order_book_history(runner_ids, max_load_limit)

for runner_idx in range(len(runners)):
    with runner_tabs[runner_idx]:
        with st.spinner("Loading Runner Data..."):
            data, game_start_time, game_end_time = get_runner_data(runner_ids[runner_idx], order_book_history)

        st.header(runners[runner_idx]['runnerName'])
        current_time = st.select_slider("View Order Book state at time", options=data.index,
                                        key=runner_ids[runner_idx], format_func=lambda x: x.time().strftime("%r"))
        fig = go.Figure()
        limit = 10
        fig.add_bar(x=data.loc[current_time]["ATB Price"][-limit:], y=data.loc[current_time]["ATB Volume"][-limit:],
                    name="ATB", marker_color="blue")
        fig.add_bar(x=data.loc[current_time]["ATL Price"][:limit], y=data.loc[current_time]["ATL Volume"][:limit],
                    name="ATL", marker_color="red")
        fig.update_layout(title="Order Book", xaxis_title="Price", yaxis_title="Volume")
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Price")
        st.line_chart(data, y="Close")
        st.subheader("Volume")
        st.bar_chart(data, y="Volume")
        st.subheader("Total Volume")
        st.line_chart(data, y="Total Volume")
