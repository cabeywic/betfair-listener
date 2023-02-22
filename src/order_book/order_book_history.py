from typing import Dict, List
from order_book.runner_order_book import RunnerOrderBook


class RunnerOrderBookHistory:
    """Maintains the order book history for a runner"""

    def __init__(self, runner_id: int) -> None:
        self.runner_id = runner_id
        self.timestamps = []
        self.ltp_history = []
        self.tv_history = []
        self.delta_tv_history = []
        self.atb_price_history = []
        self.atb_volume_history = []
        self.atl_price_history = []
        self.atl_volume_history = []
        self.trd_history = []
        self.curOrderBook = RunnerOrderBook(runner_id)

    def update(self, timestamp: str, packet: dict):
        self.curOrderBook.update(timestamp, packet)
        self.timestamps.append(timestamp)
        self.ltp_history.append(self.curOrderBook.ltp)
        self.tv_history.append(self.curOrderBook.tv)
        self.delta_tv_history.append(self.curOrderBook.delta_tv)

        self.atb_price_history.append([price for price, _ in self.curOrderBook.atb_ladder])
        self.atl_price_history.append([price for price, _ in self.curOrderBook.atl_ladder])

        self.atb_volume_history.append([volume for _, volume in self.curOrderBook.atb_ladder])
        self.atl_volume_history.append([volume for _, volume in self.curOrderBook.atl_ladder])

        self.trd_history.append(self.curOrderBook.trd_ladder)


class MarketOrderBookHistory:
    """Maintains the order book state for a market"""

    def __init__(self, runner_ids: List[int]) -> None:
        self.runners: Dict[str: RunnerOrderBookHistory] = {}  # Runner ID
        self._num_records = 0
        for runner_id in runner_ids:
            self.runners[runner_id] = RunnerOrderBookHistory(runner_id)

    def get_runner_order_book(self, runner_id: int) -> RunnerOrderBookHistory:
        return self.runners[runner_id]

    def update(self, timestamp: str, packet: dict) -> None:
        self._num_records += 1
        for runner_id in self.runners.keys():
            self.runners[runner_id].update(timestamp, packet)

    def __len__(self):
        return self._num_records
