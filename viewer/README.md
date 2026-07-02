# Doc Result Viewer

A small, dependency-free static web app for browsing extraction result JSON files
(invoice / packing list / doc classification / anything else) instead of reading raw
JSON. Pure HTML/CSS/JS — no build step, no framework, no npm install.

## Running it

From this directory:

```
python3 -m http.server 8080
```

then open `http://localhost:8080/`.

You can also open `index.html` directly via `file://` — everything runs client-side
off the uploaded `File` object. Monaco Editor (used only for the raw JSON view) is
loaded from a CDN (jsdelivr), so an internet connection is required for that one path;
all other doc types work fully offline.

## What it does

1. Upload a single `.json` result file (drag-and-drop or file picker).
2. The doc type is auto-detected from `result.jsonData`:
   - `invoiceDate` present → **Invoice**
   - `packingListDate` present → **Packing List**
   - `classificationGroups` array present → **Doc Classification**
   - otherwise → raw JSON, shown read-only in Monaco (folding/expand-collapse supported)
3. Known types render a header (key/value) section plus a sortable/filterable detail
   table for line items. Tables support:
   - Zebra-striped rows
   - CSV export of the currently filtered+sorted view
   - Single-column sort (click a header: ascending → descending → original order)
   - Advanced multi-column sort (via the "Advanced sort" panel)
   - Column filtering (AND across multiple active filters, case-insensitive contains)
   - Independent "Reset sorting" / "Reset filtering" / "Reset all"
   - An "Extra" badge per row (dynamic key/value props) that opens a detail dialog
4. Theme: Light / Dark / System (default), persisted in `localStorage`.

## Known limitations

- No sample data in this repo has `isMultipleInvoices: true` / `isMultiplePackingLists: true`,
  so that rendering branch has only been manually spot-checked against a hand-edited copy
  of a sample file, not a real extraction result.
- The packing list item table is wide (20 columns); it scrolls horizontally rather than
  offering column visibility toggles.
