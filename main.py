#!/usr/bin/env python3

import redis
import json
import sys

from aiohttp.web_middlewares import middleware
from aiohttp import web


@middleware
async def validate_params_middleware(request, handler):
    """
    Middleware for data validation
    """
    if request.path == "/convert":
        from_currency = request.query.get("from")
        to_currency = request.query.get("to")
        amount_currency = request.query.get("amount")

        errors = []
        if not from_currency:
            errors.append("Parameter 'from' is required")
        if not to_currency:
            errors.append("Parameter 'to' is required")
        if not amount_currency:
            errors.append("Parameter 'amount' is required")
        else:
            try:
                amount_currency = float(amount_currency)
                if amount_currency < 0:
                    errors.append("Parameter 'amount' must be positive")
            except ValueError:
                errors.append("Parameter 'amount' must be a number")

        if errors:
            return web.json_response({"errors": errors}, status=400)

        request["from_currency"] = from_currency
        request["to_currency"] = to_currency
        request["amount_currency"] = amount_currency

        return await handler(request)

    elif request.path == "/database":
        try:
            data = await request.json()
        except json.decoder.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON data"}, status=400)

        for currency, rate in data.items():
            if not isinstance(currency, str):
                return web.json_response(
                    {"error": "Currency code must be a string"}, status=400
                )
            if not isinstance(rate, (int, float)):
                return web.json_response(
                    {"error": "Exchange rate must be a number"}, status=400
                )

        request["data"] = data

        return await handler(request)

    else:
        return await handler(request)


async def convert_handler(request):
    """
    GET request handler

    Retrieves "from", "to" and "amount" from the request. Retrieves currency values from Redis and converts amount.
    Response in json format
    """
    from_currency = request["from_currency"]
    to_currency = request["to_currency"]
    amount_currency = request["amount_currency"]

    from_rate = float(redis_client.get(from_currency))
    to_rate = float(redis_client.get(to_currency))

    converted_amount = amount_currency * to_rate / from_rate

    return web.json_response(
        {
            "from": from_currency,
            "to": to_currency,
            "amount": amount_currency,
            "converted_amount": converted_amount,
        }
    )


async def database_handler(request):
    """
    POST request handler

    If merge = 0 invalidates the data in the database and writes the data to database.
    In the body of the request you need to pass the data in json format. In which {currency code: exchange rate}
    is betrayed
    Example:
    {
        "USD": 1,
        "EUR": 1.18,
    }
    """
    merge = int(request.query.get("merge", 0))

    data = request["data"]

    if merge == 0:
        redis_client.flushdb()

    for currency, rate in data.items():
        redis_client.set(currency, rate)

    return web.json_response({"success": True})


# Currently working locally on port 8080
app = web.Application()
redis_client = redis.Redis(host="localhost", port=6379)

if not redis_client.ping():
    sys.exit("Redis server is not running")

app.middlewares.append(validate_params_middleware)
app.router.add_get("/convert", convert_handler)
app.router.add_post("/database", database_handler)

if __name__ == "__main__":
    web.run_app(app)
