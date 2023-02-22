import logging
import queue
import threading
import random
from tenacity import retry, wait_exponential
from datetime import datetime
from dataclasses import dataclass
import betfairlightweight
from betfairlightweight import StreamListener
from betfairlightweight import BetfairError


class Streaming(threading.Thread):
    def __init__(
            self,
            client: betfairlightweight.APIClient,
            market_filter: dict,
            market_data_filter: dict,
            conflate_ms: int = None,
            streaming_unique_id: int = 1000,
            output_queue: queue.Queue = None,
    ):
        threading.Thread.__init__(self, daemon=True, name=self.__class__.__name__)
        self.client = client
        self.market_filter = market_filter
        self.market_data_filter = market_data_filter
        self.conflate_ms = conflate_ms
        self.streaming_unique_id = streaming_unique_id
        self.stream = None
        if output_queue:
            self.output_queue = output_queue
        else:
            self.output_queue = queue.Queue()
        self.listener = StreamListener(output_queue=self.output_queue)

    @retry(wait=wait_exponential(multiplier=1, min=2, max=20))
    def run(self) -> None:
        self.client.login()
        self.stream = self.client.streaming.create_stream(
            unique_id=self.streaming_unique_id, listener=self.listener
        )
        try:
            self.streaming_unique_id = self.stream.subscribe_to_markets(
                market_filter=self.market_filter,
                market_data_filter=self.market_data_filter,
                conflate_ms=self.conflate_ms,
                initial_clk=self.listener.initial_clk,  # supplying these two values allows a reconnect
                clk=self.listener.clk,
            )
            self.stream.start()
        except BetfairError:
            logging.error("BetfairError - Check connection")
            raise
        except Exception:
            logging.critical("Streaming stopped unexpectedly")
            raise

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()


@dataclass
class StreamConfig:
    start_time: datetime
    stream_name: str
    market_filter: dict
    stream_market_filter: dict
    is_running: bool = False

    @property
    def streaming_unique_id(self) -> int:
        return random.randint(0, 10000)
