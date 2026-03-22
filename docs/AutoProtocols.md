What do we need:
Well we need access to the libre-linkup datastream
We definitely need to maintain all that fucking data somewhere
We need to record stuff like feeding, injecting, exercise, sunning
We need glucose, we need deltas, we deltas over a 5-10 minute period
We need to handle sensor errors and temporary loss of signal
We need to be able to notify me, sometimes persistently and irritatingly, beyond "DO NOT DISTURB", and we need to intervene automaitcally if I do not or cannot respond.
We need to know the time
Let's also calculate a second derivative of glucose
Processing Sensor Artifacts (e.g. random dip down and back up - maybe we care to process something differently, maybe we don't, I'm not sure)

We know how much insulin got in when and there's a little overlap of depots. 

Hidden variables:
- insulin concentration in the blood
- insulin remaining in the depot
- rate of insulin release intrinsic to the site
- general circulatory variable (has to do with insulin absorption based on body state - e.g. exericise)
- carbohydrate absorption rate/curve
- maybe a few forecast variables idk if I care.




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

Depending on mode we tolerate different levels of risk. I think that's the main thing to optimize in the model is just, I don't want him to drop below 60 like ever, ESPECIALLY when I'm not around. If I'm around it's like, well, I can still technically rescue. I never want him below 40 or whatever, that's pretty catastrophic no matter what happens but... I guess it's still a lot worse if i'm not there. 

