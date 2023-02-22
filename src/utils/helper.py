import betfairlightweight
from betfairlightweight.filters import (
    streaming_market_filter,
    streaming_market_data_filter,
)
import logging
from datetime import datetime
from typing import List, Dict
from utils.configure import get_market_filter_config


def get_events(trading: betfairlightweight.APIClient, event_filter: dict) -> List[Dict]:
    """Get list of events and markets from Betfair API

    Args:
        trading (betfairlightweight.APIClient): Betfair API client
        event_filter (dict): Event filter

    Returns:
        List[Dict]: List of events and markets
    """

    all_events = trading.betting.list_events(
        filter=event_filter,
        lightweight=True
    )

    res = []

    for event in all_events:
        event = event["event"]

        market_filter = event_filter.copy()
        market_filter["eventIds"] = [event["id"]]

        logging.debug(f"Market Filter for {event['id']}: {market_filter}")

        markets = trading.betting.list_market_catalogue(
            filter=market_filter,
            max_results='100',
            sort='FIRST_TO_START',
            market_projection=["MARKET_DESCRIPTION", "RUNNER_DESCRIPTION", "EVENT_TYPE"],
            lightweight=True
        )

        res.append({"event": event, "markets": markets})

    return res


def get_stream_market_filter(config):
    event_ids, event_type_ids, market_types, country_codes = get_market_filter_config(config)

    return streaming_market_filter(
        event_type_ids=event_type_ids,
        country_codes=country_codes,
        market_types=market_types,
        event_ids=event_ids
    )


def get_market_filter(config):
    event_ids, event_type_ids, market_types, country_codes = get_market_filter_config(config)
    market_filter = betfairlightweight.filters.market_filter(
        event_type_ids=event_type_ids,
        market_countries=country_codes,
        market_type_codes=market_types,
        event_ids=event_ids,
    )

    return market_filter


def convert_timestamp_to_datetime(timestamp: str) -> datetime:
    return datetime.fromtimestamp(int(timestamp)/1000)


def get_stream_market_data_filter(config):
    data_fields = config['market_data_filter']
    return streaming_market_data_filter(fields=data_fields)
