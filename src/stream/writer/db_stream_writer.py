import time
import os
from typing import List, Tuple, Dict, Any
import logging
from pymongo import MongoClient
from betfairlightweight.resources import MarketBook
from stream.writer.stream_writer import MarketBuffer


class MarketDatabaseBuffer(MarketBuffer):
    def __init__(self, market_id: str, max_size: int=10, db_uri: str="", db_name: str="qst_listener") -> None:
        super().__init__(market_id, max_size)
        self.mongodb_client = MongoClient(db_uri)
        self.database = self.mongodb_client(db_name)


    def push(self, item: MarketBook) -> None:
        self.time_start = time.time()
        self.buffer.append(item)

        # Write data if buffer is full 
        if len(self.buffer) > self.max_size:
            logging.debug(f"Writing buffer for market {item.market_id} as buffer is full")
            self.write()

    def write(self) -> None:
        if len(self) == 0 : return

        # self.database[self.market_id].insert_one(self.buffer)

        filename = f"{self.market_id}.txt"
        with open(os.path.join(self.write_path, filename), "a") as file:
            for item in self.buffer:
                data = {str(int(item.publish_time.timestamp()*1000)): item.streaming_update}
                file.write(str(data) + "\n")

        self.buffer = []


