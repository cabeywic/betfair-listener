from utils.helper import convert_timestamp_to_datetime
from typing import Dict, List
from stream.storage.data_location import DataLocation
import math
import logging


def generate_market_report(event_id: str, market_info: dict, data_location: DataLocation) -> dict:
    """Generates a report for a single market

    Args:
        event_id (str): Event ID
        market_info (dict): Event data
        data_location (DataLoader): DataLoader instance

    Returns:
        dict: Market report
    """
    market_id = market_info['marketId']
    logging.debug(f"Generating market report for {market_id}")
    market_data = {}
    # Load market data
    try:
        market_data = data_location.load_market(event_id, market_id)['mcm']
    except FileNotFoundError:
        logging.error(f"Market data not found for {market_id}")
    except KeyError:
        logging.error(f"Market data found but missing market change message {market_id}")

    # market_start_time = market_info['description']['marketTime'] TODO: Fix this
    # market_start_time = parser.isoparse(market_start_time).isoformat() TODO: Fix this

    timestamp_count = 0
    timestamp_diff_total = 0
    last_timestamp = None
    is_market_closed = False
    is_market_data_missing = False

    timestamps = list(market_data)
    for timestamp in timestamps:
        timestamp_count += 1
        timestamp = int(timestamp)

        if last_timestamp is not None:
            timestamp_diff = timestamp - last_timestamp
            timestamp_diff_total += timestamp_diff
            # Check if there is a gap of more than 10 minutes
            if timestamp_diff > 10 * 60 * 60:
                is_market_data_missing = True
        last_timestamp = timestamp

    last_timestamp = str(last_timestamp)
    # Check if market is closed
    if "marketDefinition" in market_data[last_timestamp]:
        if market_data[last_timestamp]["marketDefinition"]["status"] == "CLOSED":
            is_market_closed = True

    record_start = convert_timestamp_to_datetime(timestamps[0])
    record_end = convert_timestamp_to_datetime(timestamps[-1])
    record_length_sec = (record_end - record_start).total_seconds()

    return ({
        "market_id": market_id,
        # "market_name": market_info['name'], TODO: Fix this
        # "market_start_time": market_start_time, TODO: Fix this
        "record_start": record_start.isoformat(),
        "record_end": record_end.isoformat(),
        "record_length_sec": record_length_sec,
        "contains_market_closure": is_market_closed,
        "contains_missing_data": is_market_data_missing,
        "timestamp_count": timestamp_count,
        "timestamp_avg_diff": math.ceil(timestamp_diff_total / timestamp_count),
        "num_runners": len(market_info['runners']),
    })


def generate_event_report(event_id: str, data_location: DataLocation) -> dict:
    """Generates a report for a single event"""
    logging.info(f"Generating event report for {event_id}")
    # Load event data
    event_data = data_location.load_event(event_id)
    markets = list(event_data['markets'])

    market_report = []

    for market in markets:
        event_id = event_data["event"]["id"]
        market_report.append(generate_market_report(event_id, market, data_location))

    event_report = {
        'event_id': event_id,
        'event_name': event_data['event']['name'],
        'markets': market_report
    }

    return event_report


def generate_all_events_report(data_location: DataLocation) -> List[Dict]:
    """Generates a report for all events"""
    events = data_location.load_json_data(file_name='eventLog.json')
    report = []

    for event_id in events:
        report.append(generate_event_report(event_id, data_location))

    return report
