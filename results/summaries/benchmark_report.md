# 5G Adaptive Paging: Quantitative Benchmark Results

| Traffic Regime | Algorithm | Mean Energy (J) (95% CI) | Mean Delay (s) | P95 Delay (s) | Deadline Miss (%) | Paging Overhead | Est. Battery (Years) |
|---|---|---|---|---|---|---|---|
| Sparse Poisson | Baseline Periodic DRX (1.28s) | 0.5076 ± 0.0081 | 0.771 ± 0.013 | 1.350 | 0.00% | 0.97 | 0.25 ± 0.00 |
| Sparse Poisson | Baseline Periodic DRX (2.56s) | 0.4191 ± 0.0072 | 1.422 ± 0.027 | 2.598 | 0.00% | 0.94 | 0.31 ± 0.01 |
| Sparse Poisson | Baseline Periodic DRX (5.12s) | 0.3586 ± 0.0065 | 2.684 ± 0.081 | 5.037 | 0.00% | 0.88 | 0.36 ± 0.01 |
| Sparse Poisson | AdaPaging (Proposed Adaptive) | 0.4026 ± 0.0092 | 2.245 ± 0.073 | 5.526 | 0.64% | 0.90 | 0.32 ± 0.01 |
| Moderate Poisson | Baseline Periodic DRX (1.28s) | 1.4088 ± 0.0154 | 0.789 ± 0.005 | 1.391 | 0.00% | 0.88 | 0.09 ± 0.00 |
| Moderate Poisson | Baseline Periodic DRX (2.56s) | 1.1858 ± 0.0130 | 1.453 ± 0.012 | 2.636 | 0.00% | 0.77 | 0.11 ± 0.00 |
| Moderate Poisson | Baseline Periodic DRX (5.12s) | 0.9211 ± 0.0051 | 2.741 ± 0.020 | 5.112 | 7.27% | 0.62 | 0.13 ± 0.00 |
| Moderate Poisson | AdaPaging (Proposed Adaptive) | 1.3301 ± 0.0152 | 1.097 ± 0.024 | 2.899 | 0.07% | 0.83 | 0.09 ± 0.00 |
| Bursty Mmpp | Baseline Periodic DRX (1.28s) | 1.1466 ± 0.0191 | 0.846 ± 0.004 | 1.526 | 0.00% | 0.33 | 0.11 ± 0.00 |
| Bursty Mmpp | Baseline Periodic DRX (2.56s) | 0.7670 ± 0.0171 | 1.482 ± 0.012 | 2.735 | 0.00% | 0.23 | 0.17 ± 0.00 |
| Bursty Mmpp | Baseline Periodic DRX (5.12s) | 0.5351 ± 0.0133 | 2.752 ± 0.017 | 5.160 | 26.40% | 0.16 | 0.24 ± 0.01 |
| Bursty Mmpp | AdaPaging (Proposed Adaptive) | 1.2621 ± 0.0196 | 0.838 ± 0.019 | 2.306 | 0.68% | 0.38 | 0.11 ± 0.00 |
| Periodic | Baseline Periodic DRX (1.28s) | 0.6204 ± 0.0017 | 0.762 ± 0.009 | 1.349 | 0.00% | 1.00 | 0.20 ± 0.00 |
| Periodic | Baseline Periodic DRX (2.56s) | 0.5424 ± 0.0022 | 1.399 ± 0.017 | 2.563 | 0.00% | 1.00 | 0.23 ± 0.00 |
| Periodic | Baseline Periodic DRX (5.12s) | 0.5021 ± 0.0016 | 2.682 ± 0.059 | 5.000 | 0.00% | 1.00 | 0.25 ± 0.00 |
| Periodic | AdaPaging (Proposed Adaptive) | 0.5609 ± 0.0019 | 2.563 ± 0.039 | 5.103 | 0.00% | 1.00 | 0.22 ± 0.00 |
| Heavy Tail Pareto | Baseline Periodic DRX (1.28s) | 0.8262 ± 0.0149 | 0.760 ± 0.007 | 1.341 | 0.00% | 1.00 | 0.16 ± 0.01 |
| Heavy Tail Pareto | Baseline Periodic DRX (2.56s) | 0.7484 ± 0.0151 | 1.408 ± 0.024 | 2.558 | 0.00% | 1.00 | 0.18 ± 0.01 |
| Heavy Tail Pareto | Baseline Periodic DRX (5.12s) | 0.7060 ± 0.0141 | 2.697 ± 0.056 | 4.998 | 0.00% | 1.00 | 0.19 ± 0.02 |
| Heavy Tail Pareto | AdaPaging (Proposed Adaptive) | 0.7830 ± 0.0176 | 1.560 ± 0.026 | 3.680 | 0.17% | 1.00 | 0.17 ± 0.03 |

> **Note on Energy Reporting:** All energy metrics and battery life estimates represent modeled values derived from 3GPP TR 38.840 RF/baseband power parameters, not measured physical hardware power consumption.
