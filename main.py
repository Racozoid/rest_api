#!/usr/bin/env python3

import redis
from aiohttp import web


async def convert_handler(request):
    """
    GET request handler

    Retrieves "from", "to" and "amount" from the request. Retrieves currency values from Redis and converts amount.
    Response in json format
    """
    from_currency = request.query["from"]
    to_currency = request.query["to"]
    amount_currency = float(request.query["amount"])

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

    If merge = 0 invalidates the data in the database and writes the data to database
    """
    merge = int(request.query.get("merge", 0))

    data = await request.json()

    if merge == 0:
        redis_client.flushdb()

    for currency, rate in data.items():
        redis_client.set(currency, rate)

    return web.json_response({"success": True})


# Currently working locally on port 8080
app = web.Application()
redis_client = redis.Redis(host="localhost", port=6379)

app.router.add_get("/convert", convert_handler)
app.router.add_post("/database", database_handler)

if __name__ == "__main__":
    web.run_app(app)
