What do we need:
Well we need access to the libre-linkup datastream
We definitely need to maintain all that fucking data somewhere
We need to record stuff like feeding, injecting, exercise, sunning
We need glucose, we need deltas, we deltas over a 5-10 minute period
We need to handle sensor errors and temporary loss of signal
We need to be able to notify me, sometimes persistently and irritatingly, beyond "DO NOT DISTURB", and we need to intervene automaitcally if I do not or cannot respond.
We need to know the time
Let's also calculate a second derivative of glucose

Hidden variables:
- insulin currently active in bloodstream
- insulin remaining in the depot
- rate of insulin release
- carbohydrate absorption rate/curve
- digestion timing
- exercise effects
- site variability
- sensor artifacts


| Observation | Interpretation |
|--------------|---------------|
| rising glucose | sugar absorption > insulin effect |
| falling glucose | insulin effect > sugar absorption |
| flat glucose | roughly balanced pressures |
| high volatility | both sugar and insulin effects may be large |

dG/dt ≈ sugar_pressure − insulin_pressure
But those pressures are hidden.
The system only observes the **net result**.

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

-> Yeah so this is what chatgpt wrote, but... honestly I have the feeling that the gamma is pretty good. 
the issue is that the gamma is like... there's some variability as to what kind of gamma you have, and then you have the ability to kinda "ride" the gamma, like speeding it up artificially you know? forcing it along in time a little faster, e.g. with exercise I think... and also if the depot kinda sits, you can get "stuck" on the gamma, where one process starts moving along without the rest. 
Because of this, I'm inclined to do kind of a decomposed gamma, I think, where we pay some attention to the separate parameters. 

Carb effects are probably gamma too, but they're typically very regular, maybe some dependence on GI state (e.g. is he sick)

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
