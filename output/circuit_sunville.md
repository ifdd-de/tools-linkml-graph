
|Slot|Value|
|---|---|
|model_name[?](https://example.org/grid/assets/model_name)|Example excerpt Sunville-Loadstead|

## locations


|location_type|place|id|name|description|
|---|---|---|---|---|
|Substation|Sunville|SUB-SNV|Sunville substation|380/110 kV substation at the western edge of Sunville. Grid connection point of the example circuit.|
|Substation|Loadstead|SUB-LST|Loadstead substation|380/110 kV substation supplying the town of Loadstead. End point of the example circuit.|
|SwitchingStation|Midfield|SWS-MID|Midfield switching station|Switching station without transformation, route midpoint.|

## assets


|asset_type|voltage_kv|commissioned_on|installed_at|part_of_circuit|id|name|description|
|---|---|---|---|---|---|---|---|
|PowerTransformer|380|1998-06-15|[SUB-SNV](SUB-SNV)||AST-T1|Transformer T1|300 MVA power transformer, 380/110 kV, built in 1998.|
|PowerTransformer|380|2003-09-01|[SUB-LST](SUB-LST)||AST-T2|Transformer T2|300 MVA power transformer, 380/110 kV, built in 2003.|
|CircuitBreaker|380|2010-04-20|[SUB-SNV](SUB-SNV)|[CIR-380-01](CIR-380-01)|AST-Q1|Circuit breaker Q1|SF6 circuit breaker in the Sunville feeder bay.|
|OverheadLine|380|1998-06-15||[CIR-380-01](CIR-380-01)|AST-L1|Overhead line L-380-01|Overhead line section Sunville-Midfield, quad bundle, 42 km.|
|Cable|380|2015-11-30|[SWS-MID](SWS-MID)|[CIR-380-01](CIR-380-01)|AST-C1|Cable C-380-01|Underground cable section Midfield-Loadstead, XLPE, 8 km.|

## circuits


|voltage_kv|from_location|to_location|id|name|description|
|---|---|---|---|---|---|
|380|[SUB-SNV](SUB-SNV)|[SUB-LST](SUB-LST)|CIR-380-01|Circuit Sunville-Loadstead|380 kV circuit between Sunville and Loadstead substation. Fictional example for documentation purposes.|
