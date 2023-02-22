import os
import glob
from typing import List, Dict, Union, Any
import logging
import json
from abc import ABC, abstractmethod


class AbstractDataStorage(ABC):
    """Abstract base class for data storage"""
    @abstractmethod
    def create(self):
        pass

    @abstractmethod
    def load_events(self) -> List[Dict]:
        pass

    @abstractmethod
    def load_event(self, event_id: str) -> Dict:
        pass

    @abstractmethod
    def load_market(self, event_id: str, market_id: str) -> Dict:
        pass


class DataLocation(AbstractDataStorage):
    """Class to handle the creation of data folders and files"""

    def __init__(self, data_path: str, events: List[Dict]):
        self.data_path = data_path
        self.events = events
        market_event_mapping = {}
        for event in events:
            for market in event["markets"]:
                market_event_mapping[market["marketId"]] = event["event"]["id"]
        self.market_event_mapping = market_event_mapping

    def create(self):
        """ Create data folders and files """
        self._create_event_folders()
        self._create_main_event_log()

        for event in self.events:
            self._create_event_index(event)

    def _create_event_folders(self):
        logging.info("Creating event folders")
        for event in self.events:
            self._create_folder(event["event"]["id"])

    def _create_main_event_log(self):
        """ Check if event log exists if so load and append missing events, else create new """

        logging.info("Creating main event log")
        file_name = "eventLog.json"
        event_log = {}

        if self.check_file_exists("", file_name):
            # Load file and append missing events
            with open(os.path.join(self.data_path, file_name), "r") as file:
                event_log = json.load(file)
            for event in self.events:
                if event["event"]["id"] not in event_log.keys():
                    event_log[event["event"]["id"]] = event["event"]["name"]
        else:
            event_log = {event["event"]["id"]: event["event"]["name"] for event in self.events}

        # Write to file
        self.save_json_data(event_log, file_name=file_name)

    def _create_event_index(self, event: Dict[str, Union[Dict, List]]) -> None:
        """ Create event index file for an event, if exists append missing markets

        Args:
            event (Dict[str: Dict]): Event object from Betfair API w/ markets
        """
        logging.info(f"Creating event index for {event['event']['name']}")

        res = {"event": event["event"]}
        file_name = "eventIndex.json"
        relative_file_path = os.path.join(f"{event['event']['id']}/", file_name)

        if self.check_file_exists(f"/{event['event']['id']}/", file_name):
            # Load file and append missing markets
            with open(os.path.join(self.data_path, relative_file_path), "r") as file:
                cur_event_index = json.load(file)

            markets: List[Dict] = cur_event_index["markets"]
            cur_market_ids: List[str] = [market["marketId"] for market in markets]

            for market in event["markets"]:
                if market["id"] not in cur_market_ids:
                    markets.append(market)

            res["markets"] = markets
        else:
            res["markets"] = event["markets"]

        # Write to file
        self.save_json_data(res, folder_name=event["event"]["id"], file_name=file_name)

    def check_file_exists(self, relative_path: str, file_name: str) -> bool:
        """Check if file exists in relative path from data folder

        Args:
            relative_path (str): Path relative to data folder
            file_name (str): File name

        Returns:
            bool: True if file exists
        """
        file_path = os.path.join(self.data_path, relative_path, file_name)
        return os.path.exists(file_path)

    def load_json_data(self, folder_name: str = None, file_name: str = "eventIndex.json"):
        """Loads data from json file relative to the root directory.

        Args:
            folder_name (str, optional): Sub directory inside the root folder. Defaults to None.
            file_name (str, optional): Valid filename. Defaults to "eventIndex.json".

        Returns:
            Any: JSON data
        """
        if folder_name is None:
            file = os.path.join(self.data_path, file_name)
        else:
            file = os.path.join(self.data_path, folder_name, file_name)
        with open(file) as f:
            data = json.load(f)
        return data

    def load_events(self) -> List[Dict]:
        """Returns all events

        Returns:
            List[Dict]: List of events
        """
        if len(self.events) > 0:
            return self.events
        else:
            return self.load_json_data(file_name="eventLog.json")

    def save_json_data(self, data: Any, folder_name: str = None, file_name: str = "eventIndex.json") -> None:
        """Saves data to json file relative to the root directory.

        Args:
            data (Any): Data to save
            folder_name (str, optional): Sub directory inside the root folder. Defaults to None.
            file_name (str, optional): Valid filename. Defaults to "eventIndex.json".
        """
        if folder_name is None:
            file = os.path.join(self.data_path, file_name)
        else:
            file = os.path.join(self.data_path, folder_name, file_name)

        with open(file, "w") as file:
            file.write(json.dumps(data, indent=4))

    def load_event(self, event: str) -> Dict:
        """Loads event data from json file relative to the root directory.

        Args:
            event (str): Event ID

        Returns:
            Any: JSON data
        """
        return self.load_json_data(folder_name=event)

    def load_market(self, event: str, market: str) -> Dict:
        """Loads market data from json file relative to the root directory.

        Args:
            event (str): Event ID
            market (str): Market ID

        Returns:
            Any: JSON data
        """

        if not market.endswith('.json'):
            market += '.json'
        return self.load_json_data(folder_name=event, file_name=market)

    def _create_folder(self, folder_name: str, relative_path: str = "") -> None:
        """Create folder in relative path from data folder
        
        Args:
            folder_name (str): Name of folder to create
            relative_path (str, optional): Path relative to data folder. Defaults to "".
        """
        folder_path = os.path.join(self.data_path, relative_path, folder_name)
        logging.info(f"Creating folder at {folder_path}")
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

    def get_files_in_folder(self, folder_name: str = "", file_extension="txt") -> List[str]:
        folder_path = os.path.join(self.data_path, folder_name, f"**/*.{file_extension}")
        print(folder_path)
        return glob.glob(folder_path, recursive=True)
