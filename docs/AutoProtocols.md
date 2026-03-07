# Benny Care System – Metabolic Monitoring and Intervention Design Notes

These notes summarize the major concepts discussed while designing the automated monitoring and feeding system for Benny. The goal is **safe autonomous supervision when Benny is unattended**, not perfect physiological modeling.

---

# 1. System Goal

The system is a **closed-loop supervisory controller** for a biological process.

Its responsibilities are:

1. Monitor glucose continuously.
2. Estimate short-term metabolic behavior.
3. Apply conservative safety rules when Benny is unattended.
4. Notify the human operator before acting when possible.
5. Intervene automatically if the operator does not respond.

The system must prioritize **life safety over optimal metabolic control**.

---

# 2. Observability Problem

The key challenge is that the system does not directly observe the important physiological variables.

Hidden variables include:

- insulin currently active in bloodstream
- insulin remaining in the depot
- rate of insulin release
- carbohydrate absorption rate
- digestion timing
- exercise effects
- site variability
- sensor artifacts

Instead, the system only observes:

- glucose readings
- time history
- feeding events
- insulin events
- behavior/activity signals (optional)

This means the system must **infer hidden state from observed behavior**.

---

# 3. Observed Signals

The most useful signals from the glucose sensor are not just the raw value but its derivatives.

Important observables:

- glucose level
- slope (rate of change)
- acceleration (change in slope)

Approximate calculations:

```
slope ≈ (G_now − G_10min_ago) / 10
accel ≈ slope_now − slope_10min_ago
```

Interpretation:

| Observation | Interpretation |
|--------------|---------------|
| rising glucose | sugar absorption > insulin effect |
| falling glucose | insulin effect > sugar absorption |
| flat glucose | roughly balanced pressures |
| high volatility | both sugar and insulin effects may be large |

---

# 4. Net Metabolic Pressure

Conceptually the system behaves like:

```
dG/dt ≈ sugar_pressure − insulin_pressure
```

But those pressures are hidden.

The system only observes the **net result**.

---

# 5. Metabolic Activity Level

One critical insight from observation:

Large swings tend to occur when **both insulin and sugar effects are high simultaneously**.

Example pattern:

```
+10 mg/dL rise
then
-7 mg/dL drop
within ~30 minutes
```

This indicates a **high metabolic throughput state**.

Two hidden quantities therefore matter:

```
direction = sugar_pressure − insulin_pressure
activity  = sugar_pressure + insulin_pressure
```

Direction determines slope.

Activity determines volatility and sensitivity.

---

# 6. Event-Based Physiology

The system should track discrete metabolic events:

## Insulin Events
```
time
dose
injection site
```

## Feed Events
```
honey (fast carb)
cookies (medium carb)
kibble (slow carb)
```

## Exercise Events
Optional modifier affecting insulin activation.

## Sensor Events
Glucose readings.

---

# 7. Kernel / Curve Modeling

Gamma-like curves can approximate effect timing but should not be treated as exact physiology.

They are useful for:

- plausible rise/fall shapes
- timing structure
- scaling effects with dose

They should be treated as **baseline kernels** and then adjusted dynamically.

Example:

```
effective_insulin =
    insulin_kernel(time_since_shot)
    × site_factor
    × activation_factor
    × exercise_factor
```

Carb effects are similar:

```
fast_carbs → honey
medium_carbs → cookies
slow_carbs → kibble
```

---

# 8. Hidden State Estimation

The system should maintain an internal estimate such as:

```
MetabolicEstimate

glucose
glucose_slope
glucose_accel

nominal_insulin_on_board
effective_insulin_pressure

fast_carb_pressure
medium_carb_pressure
slow_carb_pressure

activity_level
reversal_risk
sensor_confidence

forecast_10m
forecast_15m
```

These estimates update continuously based on observed glucose behavior.

---

# 9. Forecasting

Forecasts should remain **short horizon** due to system uncertainty.

Example:

```
forecast_15 =
    current_glucose
    + slope * 15
    + adjustment_from_estimated_pressures
```

Long predictions are unreliable.

---

# 10. Safety Philosophy

The system should emphasize:

- conservative behavior
- clear deterministic rules
- human override when available
- transparency of internal state

The system should never attempt aggressive metabolic optimization.

Its role is **preventing dangerous lows when Benny is unattended**.

---

# 11. Dashboard Observability

The monitoring dashboard should expose:

- glucose
- slope
- estimated insulin pressure
- carb pressures
- activity level
- forecast
- intervention cooldown
- last intervention
- event log

This allows human supervision and debugging.

---

# 12. Practical Autonomous Protocol

A simpler autonomous intervention protocol was proposed for unattended operation.

The system first asks the operator before acting.

If the operator does not respond in time, the system intervenes.

## Below 100 mg/dL

```
Send notification to server.

If no response within 10 minutes
AND glucose has not risen significantly:

    dispense:
        1 kibble bin
        cookie dust dose
```

Purpose: small stabilization snack.

---

## Below 80 mg/dL

```
Send notification.

If no response within 5 minutes
AND glucose not increasing:

    dispense:
        10g honey
        cookies
        1 kibble bin
```

Purpose: moderate correction.

---

## Below 70 mg/dL

```
Send notification.

If no response within 2 minutes:

    dispense:
        15g honey
        cookies
        1 kibble bin
```

Purpose: urgent correction.

---

## Below 60 mg/dL

```
Send notification.

If no response within 2 minutes:

    dispense:
        20g honey
        cookies
        1 kibble bin
```

Purpose: aggressive rescue.

---

## Re-check behavior

```
If <70 or <60 event occurred:

re-check glucose every 10 minutes
repeat rescue protocol if needed
```

This ensures corrections have time to act before repeating.

---

# 13. Human-in-the-Loop Design

When the human operator is available:

- they can override feeding decisions
- they can supervise high-volatility metabolic states
- they can handle "insulin clearout" events

The autonomous system only needs to handle **unattended safety scenarios**.

---

# 14. Engineering Architecture

System components:

```
sensor → telemetry
      → estimator
      → policy engine
      → action queue
      → actuators
      → webcam verification
      → event log
      → dashboard
```

The estimator and policy should remain separate.

---

# 15. Key Engineering Insight

The goal is **not perfect physiology modeling**.

The goal is:

```
reliable detection of dangerous trends
+
conservative automatic intervention
```

Saving a life does not require a perfect model, only a **safe one**.