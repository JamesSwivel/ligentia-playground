### **Ligentix AI Automation Toolbox Schedule**

| # | Milestone | Timeline | Status |
| --- | --- | --- | --- |
| 1 | **Feasibility Study** | Beg-Jul 2026 | ✅ Completed |
| 2 | **MVP** – demonstrable web GUI | Mid-Aug 2026 | 🔄 In progress |
| - | (Scenario 1-2, Part 1-2) | - | - |
| 3 | **Production System** – UAT  | 1st week Oct 2026 | 🔄 In progress |
| - | (Scenario 1-4) | - | - |

### 1. Feasibility Study (beg-Jul 2026) `completed`
- RPA logon and security token
- API Emulation instead of screen capture
- Preliminary invoice and packing list data extraction by manual AI process

### 2. MVP - A demonstrable web GUI (mid-Aug 2026)
- Covering scenario 1-2 (Part 1-2)
- Phase 1 (end Jul 2026)
  - AI Doc classification - Doc Pouch auto split by doc type, e.g. invoice, packing list, etc
  - Different layout detection on invoice and packing list.
  - single/multiple PDFs upload per booking order
- Phase 2 (1st week Aug 2026)
  - AI invoice data extraction on different layouts
  - Custom data grouping, e.g. `PO + Product Code`, `PO + Product Code + Size`, etc
  - Custom data transformation, e.g. product code transformation from product remark, QTY transformation from SKU QTY, etc
- Phase 3 (2nd week Aug 2026)
  - AI packing list data extraction on different layouts
  - Overcome packing list highly dense and small font technical challenge
  - Custom data grouping, e.g. channel handing
  - Custom data transformation, e.g. single packing list item into multiple spilt in on carton, recalculated the values (e.g. CBM, weights)
- Phase 4 (mid-Aug 2026)
  - Booking order data API retrieval
  - Discrepancy check: Ligentix API data vs AI data from source PDFs 


### 3. Production System - UAT (1st week Oct 2026)
- Based on MVP feedback, continue the development on the prod system for UAT
- Covering scenario 1-4   
  NOTE: In case scenario 3-4 needs more time, this part may be released end Oct 2026
- Frontend GUI system (end users)
- Frontend GUI system (admin users)
- Backend AI Agents
- Backend API and security system
    - Database system
    - logs and statistics
    - credit and usage module
    