# Mini-Courier Planner Runtime Benchmark

| Dataset | Parcels | Stops | Bag Cap | Max Value | Route Cost | Sort (ms) | 0/1 DP (ms) | Routing (ms) | Avg Total (ms) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| small | 6 | 5 | 13 | 306 | 71.0 | 0.0018 | 0.0122 | 0.0242 | 0.0386 |
| medium | 20 | 12 | 53 | 881 | 83.0 | 0.0038 | 0.1256 | 0.1136 | 0.2433 |
| large | 50 | 25 | 145 | 2036 | 204.0 | 0.0097 | 0.8422 | 0.5540 | 1.4063 |
| xlarge (100p, 40n) | 100 | 40 | 288 | 4180 | 325.0 | 0.0187 | 3.2513 | 1.3403 | 4.6107 |

## Total Runtime Visual Comparison
```text
small                | # 0.0386 ms
medium               | # 0.2433 ms
large                | ####### 1.4063 ms
xlarge (100p, 40n)   | ######################## 4.6107 ms
```
