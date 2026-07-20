# Dynamic EV Hosting Capacity (DHC) — Pipeline

DHC = run the existing single-snapshot EV hosting capacity at **several time points**,
then report each node's **Min / Max HC range** (its flexibility band).
The time variation comes from the loads' **loadshapes**.

## Full pipeline

```
For each timestamp ts in [t1, t2, t3, ...]:

    FREEZE the feeder at ts:
        ① pre-run OpenDSS at hour H     (Set Mode=Yearly; Set Hour=H; Solve)
           → OpenDSS applies each load's loadshape:  base kW × mult(H)
        ② store the solved load powers  (read back via the OpenDSS API)
        ③ save a static load file       (kW/kvar = solved values, loadshapes stripped)
           → Loads_hour_<ts>.dss + Master_hour_<ts>.dss   (static, fixed at hour H)

    RUN the existing snapshot HC on the frozen model
        → per-node voltage + thermal bisection
        → hosting_capacity table:  Bus | Hosting_capacity_kW | Binding_constraint

After all timestamps:

    MERGE the per-timestamp tables on "Bus"   (one HC column per timestamp)
    COMPUTE per-Bus Min / Max across timestamps   → the flexibility range
        → dynamic_ev_hc.csv
```

Result (one row per node):

| Bus   | HC_<peak> | HC_<midday> | **HC_Min** | **HC_Max** |
|-------|-----------|-------------|------------|------------|
| bus45 | 320       | 410         | **320**    | **410**    |
