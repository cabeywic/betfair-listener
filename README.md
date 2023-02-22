
# QST Listener
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://camo.githubusercontent.com/890acbdcb87868b382af9a4b1fac507b9659d9bf/68747470733a2f2f696d672e736869656c64732e696f2f62616467652f6c6963656e73652d4d49542d626c75652e737667)
[![Documentation](https://img.shields.io/badge/ref-Documentation-blue)](https://jsg71.github.io/QST_Template/)

Listener that streams market data from the Betfair API and stores the data appropriately (local/database).


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`CERTS_PATH`: Path to the open SSL certificates (refer Betfair API for more details)

`CONF_PATH`: Configuration folder path, must contain conf.yml and logging.yml files

`USERNAME`: Betfair API Username

`PASSWORD`: Betfair API Password

`APP_KEY`: Betfair API Key

The conf.yml may be configured as shown below:
```yml
paths:
  data_dir: <root_path>/data/
streams:
  - start_time: 10/02/23 23:29:00
    stream_name: Arsenal v Brentford
    market_filter:
      event_ids:
        - 32048378
      event_type_ids:
        - 1
      market_type_codes:
        - MATCH_ODDS
market_data_filter:
  - EX_ALL_OFFERS
  - EX_TRADED
  - EX_TRADED_VOL
  - EX_LTP
  - EX_BEST_OFFERS_DISP
  - EX_BEST_OFFERS
  - EX_MARKET_DEF
```

`data_dir`: Path to store stream data and parse data. If using docker compose set path to `/usr/app/data`

`streams`: A list of streams with the stream start time, an appropriate name and the relevant market filter. The `start_time` format is in `%d/%m/%y %H:%M:%S`.

`market_filter`: A market filter for the selected stream, which filters specific `event_ids`, `event_type_ids`, `market_type_codes` & `country_codes`. 




## Installation

Clone the project

```bash
  git clone https://link-to-project
```

After cloning the repo run the below command, to install dependencies and create a logs folder. 

```bash
cd qst_listener
pip install -r requirements.txt 
mkdir logs data 
touch .env
```

Add the required environment variables as shown above to the `.env` file. 
## Run Locally (CLI)

There are four main runnable components to the listener. These include the stream, report, parser and streamlit app.

### 1) Running Stream 

Start the stream, check your configuration & environment and run below command 

```bash
  python src/main.py
```

### 2) Running Parser 

Parse the data from the stream and convert to JSON format

```bash
  python src/main.py -p 
```

### 3) Running Report 

Run report to perform data quality checks and validation

```bash
  python src/main.py -r
```

### 4) Running Streamlit App 

Run streamlit app to view summary of parsed data

```bash
  streamlit run src/app.py
```

## Run Locally (Docker Compose)
Prerequisites:
- Have Docker installed on your machine
- Setup .env file, certs and conf folders 
- Ensure conf.yml `data_dir`: /usr/app/data

Run the command below to build the docker image:

```bash
docker compose build
```

Run the command below to start a docker container:

```bash
docker compose up
```

*Note: Adding `-d` flag after up, will run container in detached mode (container running in the background)*