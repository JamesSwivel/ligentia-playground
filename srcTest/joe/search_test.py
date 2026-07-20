import aiohttp
import asyncio
import json


async def main():
    JWT = ""
    with open("session.json", "r+") as f:
        temp = json.load(f)
        token = temp["oidc.user:https://identity.uat1.ligentix.net/:shipping-confirmation-portal-app"]
        temp2 = json.loads(token).get("access_token")
        print(temp2)
        JWT = temp2
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
