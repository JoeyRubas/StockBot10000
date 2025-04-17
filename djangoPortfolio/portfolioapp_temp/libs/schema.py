stock_functions = [
    {
        "name": "buy",
        "description": "Buy a given amount of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol"},
                "amount": {"type": "number", "description": "Number of shares"},
            },
            "required": ["symbol", "amount"],
        },
    },
    {
        "name": "sell",
        "description": "Sell a given amount of a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Ticker symbol"},
                "amount": {"type": "number", "description": "Number of shares"},
            },
            "required": ["symbol", "amount"],
        },
    },
    {
        "name": "get_data",
        "description": "Get info from 'market', 'headlines', or 'twitter'",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Ticker symbol",
                },
            },
            "required": ["source", "symbol"],
        },
    },
    {
        "name": "get_portfolio",
        "description": "Get the current portfolio including all owned stocks and quantities",
        "parameters": {
            "type": "object",
            "properties": {},
        },
    },
]
