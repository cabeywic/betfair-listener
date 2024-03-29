from matplotlib import pyplot as plt
from typing import List, Tuple


class RunnerOrderBook:
    """Maintains the order book state for a runner"""

    def __init__(self, runner_id: int) -> None:
        self.runner_id = runner_id  # Runner ID
        self.timestamp = None  # Current timestamp
        self.atb_book = {}  # Available to back book
        self.atl_book = {}  # Available to lay book
        self.trd_book = {}  # Trades book
        self.ltp = 0  # Last traded price
        self.tv = 0  # Total volume
        self.delta_tv = 0  # Volume traded since last update

    @property
    def atb_ladder(self) -> List:
        # Available to back ladder
        atb_ladder = sorted([[price, volume] for price, volume in self.atb_book.items()], key=lambda x: x[0])
        return atb_ladder

    @property
    def atl_ladder(self) -> List:
        # Available to lay ladder
        atl_ladder = sorted([[price, volume] for price, volume in self.atl_book.items()], key=lambda x: x[0])
        return atl_ladder

    @property
    def trd_ladder(self):
        # Trades ladder
        trd_ladder = sorted(list(self.trd_book))
        return trd_ladder

    def _update_book(self, book: dict, delta_book: dict) -> None:
        if len(delta_book) > 0:
            if len(book) == 0:
                book = book.update({price: volume for price, volume in delta_book})
            else:
                for price, volume in delta_book:
                    if volume == 0 and price in book.keys():
                        # Remove price from book
                        del book[price]
                    else:
                        book[price] = volume

    def update(self, timestamp: str, packet: dict) -> None:
        """Update the order book state for a runner

        Args:
            timestamp (str): Timestamp of the update
            packet (dict): Data packet from Betfair API containing the update
        """
        if 'rc' in packet:
            self.timestamp = timestamp
            runner = [runner for runner in packet['rc'] if runner['id'] == self.runner_id]
            # print([runner['id'] for runner in packet['rc']])

            if len(runner) > 0:
                runner = runner[0]
                atb = runner.get('atb', [])
                atl = runner.get('atl', [])
                trd = runner.get('trd', [])

                self.ltp = runner.get('ltp', self.ltp)
                new_tv = runner.get('tv', self.tv)
                self.delta_tv = max(new_tv - self.tv, 0)
                self.tv = new_tv

                self._update_book(self.atb_book, atb)
                self._update_book(self.atl_book, atl)
                self._update_book(self.trd_book, trd)

    def view(self, limit=0):
        """ View the current status of the order book for a runner

        Args:
            limit (int, optional): Limit the number of prices to display. Defaults to all.
        """
        backs = self.atb_book
        lays = self.atl_book

        backs_price, backs_volume = self._get_book_price_volume(backs, 'back', limit)
        lays_price, lays_volume = self._get_book_price_volume(lays, 'lay', limit)
        plt.figure(figsize=(12, 3))
        plt.bar(backs_price, backs_volume, color='green')
        plt.axvline(x=str(self.ltp), color='k', linewidth=1.0, linestyle='--', label='Last Traded Price')
        plt.bar(lays_price, lays_volume, color='red')
        plt.legend()
        plt.show()

    def _get_book_price_volume(self, book, order_type=None, limit=0) -> Tuple[List[float], List[float]]:
        data = sorted([[price, volume] for price, volume in book.items()], key=lambda x: x[0])

        if limit > 0:
            if order_type == 'back':
                data = data[-limit:]
            elif order_type == 'lay':
                data = data[:limit]
            else:
                raise Exception("Invalid type")

        prices = []
        volumes = []
        for price, volume in data:
            prices.append(price)
            volumes.append(volume)
        return prices, volumes
