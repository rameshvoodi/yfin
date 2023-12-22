import pandas as pd
import numpy as np
import yfinance as yf
import argparse
import matplotlib.pyplot as plt
import os


def download_stock_data(ticker, start_date, end_date):
    spx_df = yf.download(ticker, start=start_date, end=end_date)
    return spx_df["Adj Close"].resample("7D").last().ffill()


def find_local_extrema(data, window_size):
    if window_size > len(data):
        raise ValueError(
            "Window size is larger than data size. Please choose a smaller window size."
        )

    local_max = data["Adj Close"].rolling(window=window_size, center=True).max()
    local_min = data["Adj Close"].rolling(window=window_size, center=True).min()
    max_indices = data["Adj Close"] == local_max
    min_indices = data["Adj Close"] == local_min

    extrema_df = pd.DataFrame(
        {
            "Local Max": data["Adj Close"][max_indices],
            "Local Min": data["Adj Close"][min_indices],
        }
    )

    extrema_df["Local Max"] = extrema_df["Local Max"].mask(
        extrema_df["Local Max"].duplicated()
    )
    extrema_df["Local Min"] = extrema_df["Local Min"].mask(
        extrema_df["Local Min"].duplicated()
    )

    return extrema_df


def find_bear_markets(data, recovery_limit):
    bear_markets = []
    bear_start = None
    bear_end = None
    i = 0
    while i < len(data) - 1:
        bear_start = i
        bear_min = i
        bear_end = None
        in_bear_market = False
        min_value = data[i]

        for j in range(i + 1, len(data)):
            price_start = data[bear_start]
            price_now = data[j]

            if not in_bear_market:
                if price_now > price_start:
                    i = j
                    break
                elif price_now <= price_start * (1 - recovery_limit):
                    in_bear_market = True
                    bear_min = j
                    min_value = price_now

            if in_bear_market:
                if price_now < min_value:
                    min_value = price_now
                    bear_min = j
                elif price_now >= min_value * (1 + recovery_limit):
                    bear_end = j - 1
                    break

        if in_bear_market:
            percent_loss = ((min_value - price_start) / price_start) * 100
            bear_markets.append((bear_start, bear_min, bear_end, percent_loss))
            i = bear_end if bear_end else j
        else:
            i += 1

    if in_bear_market and bear_end is None:
        bear_end = len(data) - 1
        percent_loss = ((min_value - price_start) / price_start) * 100
        bear_markets.append((bear_start, bear_min, bear_end, percent_loss))

    return bear_markets


def find_optimal_window_size(data, min_window_size, max_window_size):
    optimal_window_size = min_window_size
    min_total_variance = float("inf")

    for window_size in range(min_window_size, max_window_size + 1):
        extrema_df = find_local_extrema(data, window_size)
        max_variance = extrema_df["Local Max"].var()
        min_variance = extrema_df["Local Min"].var()
        total_variance = max_variance + min_variance
        if total_variance < min_total_variance:
            min_total_variance = total_variance
            optimal_window_size = window_size

    return optimal_window_size


def identify_bull_markets(data, bear_markets):
    final_periods = []
    last_bear_end = data.index[0]
    last_bear = None

    for start, minimum, end, percent_loss in bear_markets:
        bear = {
            "Market Type": "Bear",
            "Peak Date": data.index[start],
            "Trough Date": data.index[minimum],
            "Peak Price": data[start],
            "Trough Price": data[minimum],
            "Percent Loss": percent_loss,
            "Number Of Days": (data.index[end] - data.index[start]).days
            if end
            else (data.index[-1] - data.index[start]).days,
        }
        if last_bear is None:
            start_value = data.loc[last_bear_end]
            start_date = last_bear_end
        else:
            start_value = last_bear["Trough Price"]
            start_date = last_bear["Trough Date"]
        end_value = data.loc[bear["Peak Date"]]
        end_date = bear["Peak Date"]
        if last_bear_end < bear["Peak Date"]:
            final_periods.append(
                {
                    "Market Type": "Bull",
                    "Trough Date": start_date,
                    "Peak Date": end_date,
                    "Trough Price": start_value,
                    "Peak Price": end_value,
                    "Percent Gain": ((end_value - start_value) / start_value) * 100,
                    "Number Of Days": (end_date - start_date).days,
                }
            )
        final_periods.append(bear)
        last_bear = bear
        last_bear_end = bear["Trough Date"]
    if last_bear_end < data.index[-1]:
        final_periods.append(
            {
                "Market Type": "Bull",
                "Trough Date": last_bear_end,
                "Peak Date": data.index[-1],
                "Trough Price": last_bear["Trough Price"],
                "Peak Price": data[-1],
                "Percent Gain": (
                    (data[-1] - last_bear["Trough Price"]) / last_bear["Trough Price"]
                )
                * 100,
                "Number Of Days": (data.index[-1] - last_bear_end).days,
            }
        )
    return final_periods


def create_market_summary(final_periods):
    return pd.DataFrame(final_periods)


def plot_markets(data, bear_market_df, bull_market_df):
    plt.figure(figsize=(14, 7))
    plt.plot(data.index, data, label="Price")

    for _, row in bear_market_df.iterrows():
        plt.plot(
            data.loc[row["Trough Date"] : row["Peak Date"]].index,
            data.loc[row["Trough Date"] : row["Peak Date"]],
            color="red",
            label="Bear Market",
        )

    for _, row in bull_market_df.iterrows():
        plt.plot(
            data.loc[row["Trough Date"] : row["Peak Date"]].index,
            data.loc[row["Trough Date"] : row["Peak Date"]],
            color="green",
            label="Bull Market",
        )

    plt.title("Bear and Bull Markets")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.show()


def main(recovery_limit, start_date, end_date):
    data = download_stock_data("^GSPC", start_date, end_date)
    bear_markets = find_bear_markets(data, recovery_limit)
    final_periods = identify_bull_markets(data, bear_markets)

    market_df = pd.DataFrame(final_periods)
    market_df["Trough Date"] = pd.to_datetime(market_df["Trough Date"])
    market_df["Peak Date"] = pd.to_datetime(market_df["Peak Date"])
    market_df = market_df.sort_values(by="Trough Date")

    bear_market_df = market_df[market_df["Market Type"] == "Bear"]
    bull_market_df = market_df[market_df["Market Type"] == "Bull"]

    columns_to_keep = [
        "Trough Date",
        "Peak Date",
        "Trough Price",
        "Peak Price",
        "Percent Gain",
        "Number Of Days",
    ]
    bear_market_df = bear_market_df[columns_to_keep]
    bull_market_df = bull_market_df[columns_to_keep]

    plot_markets(data, bear_market_df, bull_market_df)

    return bear_market_df, bull_market_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stock Market Analysis Script")
    parser.add_argument(
        "--recovery_limit",
        type=float,
        default=0.20,
        help="Threshold for determining the start and end of bear markets. Default is 0.20.",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        default="1927-12-29",
        help="Start date for the stock data analysis. Format: YYYY-MM-DD. Default is 1927-12-29.",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        default="2023-12-06",
        help="End date for the stock data analysis. Format: YYYY-MM-DD. Default is 2023-12-06.",
    )

    args = parser.parse_args()

    bear_market_df, bull_market_df = main(
        args.recovery_limit, args.start_date, args.end_date
    )

    bear_market_df.to_csv("bear_market.csv", index=False)
    bull_market_df.to_csv("bull_market.csv", index=False)
