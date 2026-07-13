# Ligentix AI Automation Toolbox - Planning and Schedule
The Ligentix AI Automation Toolbox is an AI powered RPA (Robotic Process Automation) web based system.

## AI Intelligent Document Processing
- AI document classification  
  e.g. invoice, packing list, etc
- Detect different structural layout per doc type  
  e.g. a variety of different invoice and packing layouts from different customers/suppliers.
- PDF processing flexibility
  - Single to multiple PDFs per booking order
  - Document pouch processing, i.e. one pdf consists of multiple combo of invoice + packing list.
  - Document page pre-processing and OCR accuracy enhancement
    e.g. de-skewing, orientation rectification, etc
- AI Data Extraction
  - Highly dense document information processing, e.g. packing list with dense and small fonts
  - Enhance OCR accuracy on dense document
  - Complicated packing list processing, e.g. per custom size
  - Custom data definitions, e.g. size, channel, etc
- Custom Data Post Processing
  - Custom post processing on AI data, e.g. transform product code from item remark.
  - Custom data grouping  
    e.g. PO + Product Code, PO + Product Code + Size, PO + Product Code + Channel, etc
  - Custom one to many packing list item processing, e.g. multiple size per carton

## RPA Security Access
- Emulate human Ligentix system logon via RPA logon screen.
- Acquire security token and perform auto toke refresh.
- Manual logon reminder alert in case of logon recaptcha event.

### Data Retrieval via API
- Emulate data retrieval via API approach.
- Higher accuracy instead of screen capture approach.
- Capture non visible extra PO fields, e.g. PO channel (e.g. wholesale, home shopping) 





