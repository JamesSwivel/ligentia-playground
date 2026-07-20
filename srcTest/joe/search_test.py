import aiohttp
import asyncio
import json
from pathlib import Path

script_dir = Path(__file__).resolve().parent
jwt_file = script_dir / "temp/jwt.txt"

async def main():
    JWT = ""
    with open(jwt_file, "r+") as f:
        JWT = f.read()
    headers = {"Authorization": f"Bearer {JWT}"}
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get("https://supplier.uat1.ligentix.net/Api/Shipments/bookingSearch/SE1208210132") as resp:
            print(resp.status)
            print(await resp.text())
        async with session.get(
            "https://supplier.uat1.ligentix.net/Api/Shipments/shipment/Details/SE1208210132"
        ) as resp:
            print(resp.status)
            print(await resp.text())


asyncio.run(main())
