# APSP Optimization Using IBM CPLEX

## Project Overview

This academic project studies optimization approaches for the **All-Pairs Shortest Paths (APSP)** problem using Python and IBM ILOG CPLEX.

**Our implementation work focuses on two Bounded models:**

1. **Bounded Monolithic**
2. **Bounded Benders Decomposition**

Four additional models are included **only as comparison baselines**. They are not claimed as original implementations by our team.

## Models Evaluated

| Model | Role |
|---|---|
| Bounded Monolithic | Our implementation |
| Bounded Benders | Our implementation |
| Quinton Monolithic | Comparison baseline only |
| Quinton Benders | Comparison baseline only |
| Bounded Quinton Monolithic | Comparison baseline only |
| Bounded Quinton Benders | Comparison baseline only |

## Experimental Setup

- **Solver:** IBM ILOG CPLEX
- **Benchmark graphs:** 20
- **Models per graph:** 6
- **Total runs:** 120
- **Solver time limit:** 120 seconds per run
- **Recorded fields:** solver status, solution period, raw objective, solver time, wall-clock time, and decomposition iterations where applicable

The results below summarize the final run recorded in `comparison(1).csv`.

## Final Experimental Results

| Model | Optimal / optimal-with-tolerance | Time limits | Other statuses | Median wall time |
|---|---:|---:|---:|---:|
| **Bounded Monolithic** | **20/20** | **0** | 0 | **3.50 s** |
| **Bounded Benders** | **11/20** | **9** | 0 | **74.37 s** |
| Quinton Monolithic | 14/20 | 6 | 0 | 2.64 s |
| Quinton Benders | 4/20 | 14 | 2 | 121.53 s |
| Bounded Quinton Monolithic | 20/20 | 0 | 0 | 1.72 s |
| Bounded Quinton Benders | 9/20 | 11 | 0 | 121.28 s |

**Notes on interpretation:**

- “Optimal / optimal-with-tolerance” counts solver statuses explicitly reported as `optimal solution`, `integer optimal solution`, or `integer optimal, tolerance`.
- Two Quinton Benders runs reported `dual sub problem optimal with unscaled infeasibilities`; these are shown as **other statuses**, not counted as successful solves.
- Median wall time is computed across **all 20 runs per model**, including runs that reached the time limit. It is not the median time *to optimality*.
- Solution periods and raw objective values are retained separately in the CSV; their interpretation may depend on the formulation.

## Main Findings

### Our Bounded Monolithic implementation

- Reached an optimal solver status for **all 20 benchmark instances**.
- Recorded a **3.50 s** median wall-clock time across the 20 runs.
- Was more consistently successful within the time limit than our Bounded Benders implementation.

### Our Bounded Benders implementation

- Reached an optimal solver status for **11 of 20 benchmark instances**.
- Reached the **120-second solver time limit** on the other 9 instances.
- Recorded a **74.37 s** median wall-clock time across all runs.

### Comparison baselines

- **Bounded Quinton Monolithic** achieved an optimal or optimal-with-tolerance status on **20 of 20 instances** and had the lowest overall median wall time (**1.72 s**).
- **Quinton Monolithic** recorded **14 of 20** optimal or optimal-with-tolerance statuses.
- The two comparison Benders variants reached the time limit on **14** and **11** instances, respectively.

## Conclusion

For the tested 20 graphs and the selected solver time limit, **our Bounded Monolithic implementation solved all instances to an optimal status**, while **our Bounded Benders implementation did so for 11 of 20**. The comparison shows that decomposition did not provide a consistent computational advantage in this experimental setup. These observations are specific to the tested benchmark set, code, and solver configuration; they should not be interpreted as a universal ranking of formulations.

## Repository Contents

The repository contains the APSP model implementations, benchmark inputs, scripts used for execution, supporting utilities, and recorded results. The **two Bounded models are our project contribution**; the other four are included strictly for experimental comparison.

## Technologies

- Python
- IBM ILOG CPLEX
- Mathematical optimization
- Benders decomposition

## Attribution

This is an academic project. The comparison implementations and any third-party benchmark materials remain attributable to their original authors. Bibliographic references and applicable source licenses should be added based on the original materials before redistributing third-party code.
