#!/usr/bin/env python

import json
import os
import swivel.common as U
import pandas as pd

S1_S01863302_res_json_file = "data/Data Extraction/Scenario 1/S01863302/api/searchBooking.res.json"

U.logD(f"reading: {S1_S01863302_res_json_file}")
js = U.readFile(S1_S01863302_res_json_file, "json")

invoiceNums = sorted([inv["invoiceNumber"] for inv in js["invoices"]])
orderNums = sorted([po["orderNumber"] for po in js["bookingPurchaseOrders"]])
orderNumsCheck = [
    (po["orderNumber"], po["linkedOrderNumber"], po["orderNumber"] == po["linkedOrderNumber"])
    for po in js["bookingPurchaseOrders"]
]
orderNumsInItems = sorted(
    list(set([item["orderNumber"] for po in js["bookingPurchaseOrders"] for item in po["bookingItems"]]))
)
orderNumsInItemsCheck = sorted(
    list(set([item["orderNumber"] for po in js["bookingPurchaseOrders"] for item in po["bookingItems"]]))
)

stats = {
    "invoiceNums": invoiceNums,
    "orderNums": orderNums,
    "orderNumsCheck": orderNumsCheck,
    "orderNumsInItems": orderNumsInItems,
}

# U.logD(f"stats={ U.toJsonStr(stats, isIndent=True)}", {"isMultiLine": True})
U.logD(f"stats={ stats}")
