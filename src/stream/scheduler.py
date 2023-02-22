import logging
import time
import threading
import queue
import pandas as pd
from typing import Dict, List, Tuple
from datetime import datetime
from betfairlightweight import StreamListener, APIClient
from random import randint
from stream.streaming import Streaming, StreamConfig


def _get_streaming_unique_id() -> int:
    return randint(0, 10000)


class Scheduler(threading.Thread):
    def __init__(self, stream_schedule: List[StreamConfig], client: APIClient, market_data_filter: Dict,
                 conflate_ms: int = None):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.stream_schedule = sorted(stream_schedule, key=lambda stream: stream.start_time)
        self.client = client
        self.active_streams = []
        self.market_data_filter = market_data_filter
        self.conflate_ms = conflate_ms
        self.output_queue = queue.Queue()

    def display(self) -> None:
        logging.info("Displaying Scheduled Streams...")
        for stream in self.stream_schedule:
            logging.info(f"{stream.stream_name} | Start Time: {stream.start_time}")
            events_df = self._get_stream_events_df(stream)
            logging.info("Found {0} events".format(len(events_df)))
            logging.info("Market IDs: {0}".format(events_df["Event ID"].values))
            print("\n", events_df, "\n")

    def _check_stream_is_active(self, current_stream: Streaming) -> bool:
        """
        Check if the stream is actively listening to any markets
        Args:
            current_stream: Stream to check

        Returns:
            Bool: True if the stream is active, False otherwise
        """
        return len([
            market for market in current_stream.listener.stream._caches.values() if not market.closed
        ]) > 0

    def _get_stream_events_df(self, stream_config: StreamConfig) -> pd.DataFrame:
        events = self.client.betting.list_events(
            filter=stream_config.market_filter
        )

        events_df = pd.DataFrame({
            'Event Name': [event_object.event.name for event_object in events],
            'Event ID': [event_object.event.id for event_object in events],
            'Country Code': [event_object.event.country_code for event_object in events],
            'Time Zone': [event_object.event.time_zone for event_object in events],
            'Open Date': [event_object.event.open_date for event_object in events],
            'Market Count': [event_object.market_count for event_object in events]
        })

        return events_df

    def run(self) -> None:
        logging.info("Starting Scheduler...")
        logging.info(f"Scheduled Streams[{len(self.stream_schedule)}]: ")

        for idx in range(len(self.stream_schedule)):
            current_stream = self.stream_schedule[idx]

            if current_stream.is_running:
                continue

            current_time = datetime.now()
            if current_time < current_stream.start_time:
                logging.info(f"Waiting for {current_stream.stream_name} to start @ {current_stream.start_time}")
                time.sleep((current_stream.start_time - current_time).total_seconds())

            logging.info(f"Starting {current_stream.stream_name} | ID: {current_stream.streaming_unique_id}")
            stream = Streaming(
                self.client,
                current_stream.stream_market_filter,
                self.market_data_filter,
                self.conflate_ms,
                current_stream.streaming_unique_id,
                self.output_queue,
            )

            stream.start()
            self.active_streams.append(stream)
            current_stream.is_running = True

        while len(self.active_streams) > 0:
            # Check if any streams have ended every 90 seconds, and update the active streams list
            _active_streams = []
            for stream in self.active_streams:
                if not self._check_stream_is_active(stream):
                    logging.info(f"Stream {stream.streaming_unique_id} has ended...")
                    stream.stop()
                else:
                    _active_streams.append(stream)

            self.active_streams = _active_streams
            time.sleep(90)

    def stop(self) -> None:
        for thread in self.active_streams:
            thread.stop()
