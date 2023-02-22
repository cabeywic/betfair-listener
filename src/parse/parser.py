import json
import os
import logging
from stream.storage.data_location import DataLocation
from typing import Dict, List


class MarketDataParser:
    def __init__(self, data_location: DataLocation):
        """ Initialise the DataParser class
        
        Args:
            data_location (DataLocation): Data location object, with data path and event list
        """
        self.data_location = data_location
        self.file_paths = data_location.get_files_in_folder()

    def parse_all(self, delete_flag: bool = False) -> None:
        """ Parse all files in the data folder

        Args:
            delete_flag (bool): Flag to delete the .txt files after parsing
        """
        for file_path in self.file_paths:
            logging.info(f"Parsing file {file_path}")
            parsed_file_data = self.parse_file(file_path)
            new_file_path = self._replace_extension(file_path, "json")

            # Write to file to json
            with open(new_file_path, "w") as file:
                file.write(json.dumps(parsed_file_data, indent=4))
            logging.info(f"Created new file {new_file_path}")

            # Remove .txt file
            logging.info(f"Removing file {file_path}")
            if delete_flag:
                os.remove(file_path)

    def parse_file(self, file_path: str) -> Dict[str, Dict]:
        """ Parse a file into a dictionary

        Args:
            file_path (str): File path to parse

        Returns:
            Dict[str, List]: Dictionary of parsed file
        """
        with open(file_path, "r") as file:
            market_data = {}
            for line in file:
                market_data.update(json.loads(line))

        res = {"mcm": market_data}
        return res

    def _replace_extension(self, file_path: str, new_extension) -> str:
        """ Replace the extension of a file path

        Args:
            file_path (str): File path
            new_extension (str): New extension (json, txt, etc)

        Returns:
            str: File path with new extension
        """
        file_path_without_extension = file_path.rsplit('.', 1)[0]
        new_file_path = file_path_without_extension + '.' + new_extension

        return new_file_path
