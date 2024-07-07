# Finance Project

This project is a web application that simulates a simple stock trading platform, allowing users to buy and sell stocks, view their portfolio, check stock prices, and see their transaction history. The application is built using Flask and uses SQLite for database management.

![screenshot 2024-07-07 13 42 15](https://github.com/svetozarv/finance/assets/106545363/e4f384a7-396e-48c6-b94a-a1bd44786417)
![screenshot 2024-07-07 13 42 10](https://github.com/svetozarv/finance/assets/106545363/d5adaa31-abf5-4af0-a38f-565dbb7c33d9)

## Features

- **User Registration and Login**: Users can register and log in to the platform.
- **Stock Quotes**: Users can look up current stock prices.
- **Portfolio Management**: Users can view their stock portfolio and the total value.
- **Buy and Sell Stocks**: Users can buy and sell stocks.
- **Transaction History**: Users can view their transaction history.

## Requirements

- Python 3.6+
- Flask
- CS50 Library for Python
- SQLite

## Installation

1. **Clone the repository**
   ```
   git clone https://github.com/svetozarv/finance.git
   ```

2. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

## Usage

1. **Run the application**
   ```
   flask run
   ```

2. Open your web browser and go to `http://127.0.0.1:5000`

## Routes

- **GET /:** Shows the user's portfolio.
- **GET /buy:** Displays the buy form.
- **POST /buy:** Buys the stock specified in the form.
- **GET /check:** Checks if a username is available.
- **GET /history:** Displays the user's transaction history.
- **GET /login:** Displays the login form.
- **POST /login:** Logs the user in.
- **GET /logout:** Logs the user out.
- **GET /quote:** Displays the quote form.
- **POST /quote:** Displays the stock quote.
- **GET /register:** Displays the registration form.
- **POST /register:** Registers a new user.
- **GET /sell:** Displays the sell form.
- **POST /sell:** Sells the stock specified in the form.

## Database

- **users:** Stores user information (id, username, hashed password, cash balance).
- **log:** Stores transaction logs (user_id, username, stocks, price, time, number).
- **users_data:** Stores user portfolio data (user_id, symbol, number of shares).

## Helpers

- **apology:** Renders an error message to the user.
- **login_required:** Ensures routes are only accessible to logged-in users.
- **lookup:** Looks up stock quotes.
- **usd:** Formats values as USD.
