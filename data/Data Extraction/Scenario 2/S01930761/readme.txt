[ data/Data Extraction/Scenario 2/S01930761/old/BV2503-0030 INV[2].PDF ]
- duplicated files


[ Manual check packing list vs screen ]

## check PO00066799 + XL
screen
                         qty    pkgs  cbm
#1 PO00066799 444094 XL  314    18    1.296
#2 PO00066799 444094 XL   46     3    0.21 
                         360    21    1.506

packing list pdf

upper XL              qty    pkgs  cbm         <-- seems to breakdown by channel
PO00066799 444094 XL  36     2     0.144
PO00066799 444094 XL  10     1     0.072
                      46     3     0.216 (match with screen #2)


bottom XL             qty    pkgs  cbm         <-- seems to breakdown by channel 
PO00066799 444094 XL  306    17    1.224
PO00066799 444094 XL    8     1    0.072
                      314    18    1.296 (match with screen #1)


[ python vs screen ]
data/Data Extraction/Scenario 2/S01930761/test.2026-06-23/test.py


For PO00066797, match with screen (mostly matched ...some decimal places are different)
('PO00066797', '444427', 'S', 'HOME SHOPPING') 290 19 1.368
('PO00066797', '444427', 'M', 'HOME SHOPPING') 541 34 2.448
('PO00066797', '444427', 'L', 'HOME SHOPPING') 439 39 2.808 
  NOTE:
  - screen is 2.88 cbm
  - the discrepancy is due to the child item that cbm is zero
  - if after proportional calc, it will be good
('PO00066797', '444427', 'XL', 'HOME SHOPPING') 241 22 1.584


('PO00066798', '444092', 'S', 'WHOLESALE') 71 4 0.252
('PO00066798', '444092', 'M', 'WHOLESALE') 120 6 0.432
('PO00066798', '444092', 'L', 'WHOLESALE') 63 3 0.216
('PO00066798', '444092', 'XL', 'WHOLESALE') 46 3 0.21599999999999997
('PO00066798', '444092', 'S', 'HOME SHOPPING') 212 11 0.7919999999999999
('PO00066798', '444092', 'M', 'HOME SHOPPING') 398 20 1.4400000000000002
('PO00066798', '444092', 'L', 'HOME SHOPPING') 315 17 1.224
('PO00066798', '444092', 'XL', 'HOME SHOPPING') 177 10 0.72

For PO00066799, match with screen
('PO00066799', '444094', 'S', 'WHOLESALE') 71 4 0.288
('PO00066799', '444094', 'M', 'WHOLESALE') 120 6 0.432
('PO00066799', '444094', 'L', 'WHOLESALE') 63 3 0.216
('PO00066799', '444094', 'XL', 'WHOLESALE') 46 3 0.21599999999999997
('PO00066799', '444094', 'S', 'HOME SHOPPING') 836 42 3.024
('PO00066799', '444094', 'M', 'HOME SHOPPING') 991 50 3.6
('PO00066799', '444094', 'L', 'HOME SHOPPING') 715 40 2.88
('PO00066799', '444094', 'XL', 'HOME SHOPPING') 314 18 1.296