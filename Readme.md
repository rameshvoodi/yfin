# Stock Market Analysis

This project uses historical stock price data from Yahoo Finance to identify bear and bull markets. It finds local extrema in the data to determine market trends. The results are saved as CSV files and visualized using matplotlib.

## Functionality

The script fetches stock price data for a specified ticker symbol, finds local maxima and minima, and uses these to identify periods of bear and bull markets.

## Installation

If you have Python installed, you can install these packages using pip:

```bash
pip install -r requirements.txt
```

## Usage

### Clone the project

First, clone the project from GitHub:

```bash
git clone https://github.com/rameshvoodi/yfin.git

cd yfin
```

To run the script, navigate to the directory containing the script and run:

```bash
python main.py --recovery_limit 0.20 --start_date 1927-12-29 --end_date 2023-12-06
```

This command will start the script with a recovery limit of 0.20 and analyze stock data from 1927-12-29 to 2023-12-06.

The script will output two CSV files: `bear_market.csv` and `bull_market.csv`, which contain the analysis results for bear and bull markets respectively and the results are plotted using matplotlib.

## Arguments

- `--recovery_limit`: Threshold for determining the start and end of bear markets. Default is 0.20.
- `--start_date`: Start date for the stock data analysis. Format: YYYY-MM-DD. Default is 1927-12-29.
- `--end_date`: End date for the stock data analysis. Format: YYYY-MM-DD. Default is 2023-12-06.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change. 