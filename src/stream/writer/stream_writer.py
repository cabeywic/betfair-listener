import time
import os
import json
from typing import List, Dict, Type
import logging
import queue
from betfairlightweight.resources import MarketBook
from stream.storage.data_location import DataLocation
from abc import ABC, abstractmethod


class MarketBuffer(ABC):
    """ Abstract class for writing streamed data to a file/database """

    def __init__(self, market_id, max_size: int = 10) -> None:
        self.buffer: List[MarketBook] = []
        self.time_start = time.time()
        self.market_id = market_id
        self.max_size = max_size

    @property
    def time_elapsed(self):
        """ Time elapsed since last push to buffer """
        return time.time() - self.time_start

    def __len__(self):
        """ Length of buffer """
        return len(self.buffer)

    @abstractmethod
    def push(self, item: MarketBook) -> None:
        """ Push item to buffer """
        pass

    @abstractmethod
    def write(self) -> None:
        pass


class MarketFileBuffer(MarketBuffer):
    """ Class for writing streamed data to a buffer and then writing to a file """

    def __init__(self, market_id, data_location: DataLocation, max_size: int = 10) -> None:
        """ Initialise the MarketFileBuffer class

        Args:
            market_id (str): Market id
            data_location (DataLocation): Data location object, uses the default data path
            max_size (int, optional): Max size of buffer. Defaults to 10.
        """
        super().__init__(market_id, max_size)
        self.data_location = data_location
        self.folder = data_location.market_event_mapping[market_id]

    def push(self, item: MarketBook) -> None:
        self.time_start = time.time()
        self.buffer.append(item)

        # Write data if buffer is full 
        if len(self.buffer) > self.max_size:
            logging.debug(f"Writing buffer for market {item.market_id} as buffer is full")
            self.write()

    def write(self) -> None:
        if len(self) == 0:
            return

        filename = f"{self.market_id}.txt"
        with open(os.path.join(self.data_location.data_path, self.folder, filename), "a") as file:
            for item in self.buffer:
                data = {str(int(item.publish_time.timestamp() * 1000)): item.streaming_update}
                file.write(json.dumps(data) + '\n')

        self.buffer = []


class MarketBufferFactory:
    """ Factory class for creating MarketBuffer objects """

    def __init__(self):
        self._register_buffer: Dict[str: MarketBuffer] = {}

    def register(self, buffer_type: str, buffer: Type[MarketBuffer]):
        """ Register a new buffer type
        
        Args:
            buffer_type (str): Type of buffer
            buffer (MarketBuffer): Buffer class
        """
        self._register_buffer[buffer_type] = buffer

    def get(self, buffer_type: str, **kwargs) -> Type[MarketBuffer]:
        """ Get a buffer class by type

        Args:
            buffer_type (str): Type of buffer

        Raises:
            KeyError: If buffer_type not type registered
        """
        if buffer_type not in self._register_buffer:
            raise KeyError(f"Buffer type {buffer_type} does not exist")

        return self._register_buffer[buffer_type](**kwargs)


class MarketStreamHandler:
    """ Class for handling market stream data """

    def __init__(self, stream_type: str, max_sleep_time: int = 2, max_time_elapsed: int = 10) -> None:
        self.write_buffers: Dict[str: MarketBuffer] = {}
        self.stream_type = stream_type
        self.max_sleep_time = max_sleep_time
        self.max_time_elapsed = max_time_elapsed
        self.buffer_factory = MarketBufferFactory()
        self.buffer_factory.register("local", MarketFileBuffer)
        # TODO: Add database buffer

    def write(self):
        """ Write all data remaining in buffers """
        for _, write_buffer in self.write_buffers.items():
            write_buffer.write()

    def process_packets(self, output_queue, max_buffer_size=10, **kwargs):
        """ Process packets from output queue and write to buffer 
        Args:
            output_queue (queue.Queue): Queue containing market book data
            max_buffer_size (int, optional): Max size of buffer before writing to file. Defaults to 10.
        """
        while True:
            try:
                new_market_books: List[MarketBook] = output_queue.get()
                logging.debug(f"Received new market books[{len(new_market_books)}]")

                for market_book in new_market_books:
                    market_id = market_book.market_id
                    if market_id in self.write_buffers.keys():
                        self.write_buffers[market_id].push(market_book)
                    else:
                        _buffer: Type[MarketBuffer] = self.buffer_factory.get(
                            self.stream_type,
                            market_id=market_id,
                            max_size=max_buffer_size,
                            **kwargs
                        )

                        self.write_buffers[market_id] = _buffer
                        self.write_buffers[market_id].push(market_book)

            except queue.Empty:
                for _, write_buffer in self.write_buffers.items():
                    # Write data if buffer has been not been updated for max_time_elapsed
                    if write_buffer.time_elapsed > self.max_time_elapsed:
                        logging.debug(
                            f"Writing buffer for market {write_buffer.market_id} as max_time_elapsed exceeded")
                        write_buffer.write()
                time.sleep(self.max_sleep_time)

            except Exception as e:
                logging.error(f"Error in market stream handler : {e}")
                raise


def generate_folder(path: str) -> None:
    """ Generate folder if it doesn't exist """
    if not os.path.exists(path):
        os.makedirs(path)
