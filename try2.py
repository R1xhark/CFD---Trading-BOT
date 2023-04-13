import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import requests
import json
import time
import trading212api

# Define function for CFD trading signal
def cfd_trade_signal(symbol):
    # Retrieve real-time data from Trading 212 API
    api_url = f"https://live.trading212.com/rest/v1.0/instruments/{symbol}"
    response = requests.get(api_url)
    if response.status_code != 200:
        raise ValueError(f"Failed to get response for symbol {symbol}")
    data = json.loads(response.text)
    current_price = float(data['quote']['ask'])

    # Conduct technical analysis
    data = yf.download(symbol, period='1y')
    data['SMA_50'] = data['Close'].rolling(window=50).mean()
    data['SMA_200'] = data['Close'].rolling(window=200).mean()
    data['Daily_Return'] = data['Close'].pct_change()
    data['Volatility'] = data['Daily_Return'].rolling(window=50).std()

    # Conduct fundamental analysis
    ticker = yf.Ticker(symbol)
    pe_ratio = ticker.info['trailingPE']
    market_cap = ticker.info['marketCap']
    book_value = ticker.info['bookValue']
    debt_to_equity = ticker.info['debtToEquity']
    current_ratio = ticker.info['currentRatio']

    # Make predictions
    current_price = data['Close'][-1]
    last_50_volatility = data['Volatility'][-1]
    last_200_sma = data['SMA_200'][-1]

    # Set buy and sell signals based on technical and fundamental analysis
    if current_price > last_200_sma and last_50_volatility < 0.1 and pe_ratio < 15 and market_cap > 1000000000 and book_value > 0 and debt_to_equity < 1 and current_ratio > 1:
        signal = 'Buy'
    elif current_price < last_200_sma and last_50_volatility > 0.2:
        signal = 'Sell'
    else:
        signal = 'Hold'

    # Visualize data
    plt.figure(figsize=(12,6))
    plt.plot(data['Close'], label='Price')
    plt.plot(data['SMA_50'], label='SMA 50')
    plt.plot(data['SMA_200'], label='SMA 200')
    plt.legend()
    plt.title('Technical Analysis for ' + symbol)

    return signal, current_price

# Accept user input for the symbol
symbol = input("Enter the symbol: ")

# Call the function to get the trading signal and current price
signal, current_price = cfd_trade_signal(symbol)

# Print the trading signal
print("Trading Signal:", signal)
#Print the trading signal
print("Trading Signal:", signal)

#Define Trading 212 account details
USERNAME = "your_username"
PASSWORD = "your_password"

#Initialize Trading 212 API client
trading212 = trading212api.Trading212(USERNAME, PASSWORD)

#Get instrument ID for the specified symbol
instrument_id = trading212.get_instrument_id(symbol)

#Get current position for the specified instrument
position = trading212.get_positions()[instrument_id]

#Place buy or sell order based on trading signal
# Place buy or sell order based on trading signal
if signal == 'Buy':
    # Calculate the amount to invest
    cash_available = trading212.get_cash_available()
    amount = cash_available * 0.25 # Invest 25% of available cash
    # Place buy order
    trading212.place_limit_order(instrument_id, amount, 'buy', float(current_price) + 0.01)
    # Set stop-loss and take-profit levels
    stop_loss = float(current_price) * 0.95
    take_profit = float(current_price) * 1.05

    # Place stop-loss and take-profit orders
    trading212.place_stop_loss_order(instrument_id, amount, 'sell', stop_loss)
    trading212.place_take_profit_order(instrument_id, amount, 'sell', take_profit)

    position = trading212.get_positions()[instrument_id]
    if position is not None:
        initial_position_size = position['positionSize']
    else:
        initial_position_size = 0
    time_in_trade = 0

    while True:
        # Wait for 1 minute
        time.sleep(60)
        time_in_trade += 60

        # Check if the position has been closed
        if position is None or position['positionSize'] == 0:
            profit_loss = 0
            break

        # Calculate profit or loss
        current_position_size = position['positionSize']
        profit_loss = (current_position_size - initial_position_size) * float(current_price)

        # Print performance metrics
        print(f"Time in trade: {time_in_trade} seconds")
        print(f"Profit/Loss: {profit_loss}")

        # Check if stop-loss or take-profit has been reached
        if float(current_price) < stop_loss or float(current_price) > take_profit:
            break

        # Get updated position information
        position = trading212.get_positions()[instrument_id]

    # Close the position
    trading212.close_position(instrument_id)
elif signal == 'Sell':
    # Get current position size for the specified instrument
    if position is not None:
        current_position_size = position['positionSize']
    else:
        current_position_size = 0
    # Close the position
    trading212.close_position(instrument_id)

    # Calculate profit or loss
    if current_position_size > 0:
        profit_loss = current_position_size * (float(current_price) - float(position['averageOpenPrice']))
    else:
        profit_loss = 0

    print(f"Profit/Loss: {profit_loss}")
else:
    print("No action required.")

#Close Trading 212 API client
trading212.close()