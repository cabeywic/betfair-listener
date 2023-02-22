from typing import Any, Dict
from enum import Enum
from datetime import datetime
import os
import yaml
import betfairlightweight
import logging.config
import dacite
from stream.streaming import StreamConfig


class ConfigLoader:
    def __init__(self, conf_path: str):
        self.conf_path = conf_path
        self.cache = {}

    def load(self, file_name="config", to_cache=False) -> Dict[str, Any]:
        """
        Loads a file with the given extension and returns a dictionary of the contents

        :param file_name: The name of the file to load
        :param to_cache: Whether to cache the file or not
        """

        if file_name in self.cache:
            return self.cache[file_name]

        config = None
        with open(os.path.join(self.conf_path, file_name + '.yml'), 'r') as stream:
            config = yaml.safe_load(stream)

        if to_cache and config:
            self.cache[file_name] = config

        return config


def load_config():
    conf_path = os.environ.get("CONF_PATH")
    certs_path = os.environ.get("CERTS_PATH")
    username = os.environ.get("USERNAME")
    password = os.environ.get("PASSWORD")
    app_key = os.environ.get("APP_KEY")

    config_loader = ConfigLoader(conf_path)
    config = config_loader.load()

    log_config = config_loader.load("logging")
    logging.config.dictConfig(log_config)

    trading = betfairlightweight.APIClient(username, password, app_key=app_key, certs=certs_path)

    return trading, config


def get_market_filter_config(config):
    market_filter = config['market_filter']
    event_ids = market_filter.get('event_ids', None)
    event_type_ids = market_filter.get('event_type_ids', None)
    market_types = market_filter.get('market_types', None)
    country_codes = market_filter.get('country_codes', None)

    return event_ids, event_type_ids, market_types, country_codes


def get_streams(config):
    streams = config['streams']
    for stream in streams:
        stream_market_filter = stream['market_filter'].copy()
        stream_market_filter['market_types'] = stream_market_filter['market_type_codes']
        del stream_market_filter['market_type_codes']

        stream['stream_market_filter'] = betfairlightweight.filters.streaming_market_filter(**stream_market_filter)
        stream['market_filter'] = betfairlightweight.filters.market_filter(**stream['market_filter'])

    def convert_to_datetime(time: str):
        return datetime.strptime(time, '%d/%m/%y %H:%M:%S')

    return [dacite.from_dict(StreamConfig, stream, dacite.Config(type_hooks={datetime: convert_to_datetime}))
            for stream in streams]
