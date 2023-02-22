import logging
import sys
from stream.writer.stream_writer import MarketStreamHandler
from stream.scheduler import Scheduler
from utils.configure import load_config, get_streams
from utils.helper import get_stream_market_data_filter, get_stream_market_filter, get_market_filter
from stream.storage.data_location import DataLocation
from parse.parser import MarketDataParser
from utils import cli
from utils.report import generate_all_events_report
from utils.helper import get_events
import dotenv

THREAD_WAIT_SEC = 5
BUFFER_SIZE = 5


def confirm_markets(scheduler: Scheduler) -> bool:
    scheduler.display()

    answer = input("Is this correct? [y/n]")
    return answer.lower() == "y"


def run_stream(config, trading, force_run_flag=False):
    logging.info("Successfully loaded config")
    trading.login()
    logging.info("Logged in to BetFair Account")

    # Create stream filters for markets and data
    # stream_market_filter = get_stream_market_filter(config)
    stream_market_data_filter = get_stream_market_data_filter(config)
    stream_schedule_config = get_streams(config)

    scheduler = Scheduler(stream_schedule_config, trading, stream_market_data_filter)

    # Check w/ user if input provided is valid
    if not force_run_flag and not confirm_markets(scheduler):
        # If market is incorrect logout of BetFair account and exit
        trading.logout()
        logging.info("Logged out of BetFair Account")
        logging.info("Exiting...")
        return

    events = []
    for stream_config in scheduler.stream_schedule:
        events += (get_events(trading, event_filter=stream_config.market_filter))

    data_location = DataLocation(config["paths"]["data_dir"], events)
    data_location.create()

    market_stream_handler = MarketStreamHandler('local', max_sleep_time=THREAD_WAIT_SEC)

    try:
        scheduler.start()
        market_stream_handler.process_packets(
            scheduler.output_queue,
            max_buffer_size=BUFFER_SIZE,
            data_location=data_location
        )
    except KeyboardInterrupt:
        logging.info("Stopping stream scheduler...")
        market_stream_handler.write()
        logging.info("Writen buffers on stream handler")
        scheduler.stop()
        logging.info("Stopped streams")
        trading.logout()
        logging.info("Logged out of BetFair Account")


def run_parser(config):
    logging.info("Running parser...")
    data_location = DataLocation(config["paths"]["data_dir"], [])
    data_parser = MarketDataParser(data_location)
    data_parser.parse_all(delete_flag=True)


def run_report(config):
    logging.info("Running report...")
    data_location = DataLocation(config["paths"]["data_dir"], [])
    report = generate_all_events_report(data_location)
#   save report in data_location
    data_location.save_json_data(report, file_name="report.json")


if __name__ == "__main__":
    sys.path.append(".")  # Adds higher directory to python modules path.
    parse_flag = cli.handle_cli_args().parse
    report_flag = cli.handle_cli_args().report
    force_run_flag = cli.handle_cli_args().force

    # Load environment variables from .env file
    dotenv.load_dotenv()
    # Load config and create API Client
    trading_client, app_config = load_config()

    if parse_flag or report_flag:
        # Run parser if --parse flag is set
        if parse_flag:
            run_parser(app_config)
        # Run report if --report flag is set
        if report_flag:
            run_report(app_config)
    else:
        logging.info("Running stream...")
        run_stream(app_config, trading_client, force_run_flag)
