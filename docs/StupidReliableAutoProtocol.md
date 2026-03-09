# Benny Care System – Autonomous Low-Glucose Safety Protocol

This protocol governs automatic feeding when Benny is unattended.

The system always attempts to notify the human operator first.  
If no response is received within the allowed window, the system performs a corrective feeding.

The primary objective is **preventing dangerous hypoglycemia**, not optimizing glucose control.

---

# 1. Key Signals

The protocol uses the following signals:

glucose  
current glucose reading (mg/dL)

slope  
rate of change of glucose (mg/dL per minute)

avg_slope_recent  
average slope over the last 10 minutes

avg_slope_previous  
average slope from 20–10 minutes ago

dramatic_increase  
boolean condition defined below

---

# 2. Dramatic Increase Definition

A dramatic increase indicates that carbohydrate absorption is currently overpowering insulin and glucose is rising rapidly.

```
dramatic_increase =

    (avg_slope_recent - avg_slope_previous >= +0.8 mg/dL/min)
    AND
    (avg_slope_recent >= +2 mg/dL/min)
```

Interpretation:

Example case:

```
20–10 minutes ago: +0.2 mg/dL/min
10–0 minutes ago:  +1.2 mg/dL/min
```

Change = +1.0 mg/dL/min → dramatic increase.

This condition suppresses automatic feeding because the system is already correcting upward.

---

# 3. General Rules

Before any automatic intervention:

1. Send notification to operator via Discord.
2. Wait for operator response for a defined time window.
3. If operator responds → system does nothing.
4. If operator does not respond → system evaluates conditions and may intervene.

All actions are logged.

---

# 4. Reading Sanity Check

To avoid reacting to sensor artifacts:

If a reading differs from both neighboring readings by more than 15 mg/dL:

```
ignore reading
request next reading
```

Example artifact pattern:

```
105
91
104
```

The middle value is likely compression or sensor noise.

Exception: values below 60 mg/dL bypass this check and trigger intervention.

---

# 5. Cooldown Rule

After any honey intervention:

```
cooldown = 10 minutes
```

During cooldown:

- No additional honey is dispensed
- System only monitors readings

Exception:

```
glucose < 55 mg/dL
```

In that case immediate intervention is allowed.

---

# 6. Intervention Levels

## Level 1 – Below 100 mg/dL

Condition:

```
glucose < 100
```

Action:

```
send notification
wait 10 minutes
```

If no response AND NOT dramatic_increase:

```
dispense:
    1 kibble bin
    cookie dust dose
```

Purpose: mild stabilization.

---

## Level 2 – Below 80 mg/dL

Condition:

```
glucose < 80
```

Action:

```
send notification
wait 5 minutes
```

If no response AND NOT dramatic_increase:

```
dispense:
    10 g honey
    cookies
    1 kibble bin
```

Purpose: moderate correction.

---

## Level 3 – Below 70 mg/dL

Condition:

```
glucose < 70
```

Action:

```
send notification
wait 2 minutes
```

If no response:

```
dispense:
    15 g honey
    cookies
    1 kibble bin
```

Purpose: urgent correction.

---

## Level 4 – Below 60 mg/dL

Condition:

```
glucose < 60
```

Action:

```
send notification
wait 2 minutes
```

If no response:

```
dispense:
    20 g honey
    cookies
    1 kibble bin
```

Purpose: aggressive rescue.

---

# 7. Post-Intervention Monitoring

After Level 3 or Level 4 intervention:

```
check glucose every 10 minutes
```

If still below threshold and not rising:

repeat appropriate intervention level.

Cooldown still applies unless glucose is critically low.

---

# 8. Logging

Every event must be logged.

Example entries:

```
AUTO_ALERT_100
AUTO_SNACK
AUTO_ALERT_80
AUTO_HONEY_10G
AUTO_ALERT_70
AUTO_HONEY_15G
AUTO_ALERT_60
AUTO_HONEY_20G
```

This creates an audit trail for debugging and monitoring.

---

# 9. Human Override

At any time the operator can:

- cancel pending intervention
- trigger manual feeding
- disable automatic protocol

---

# 10. Design Philosophy

This system is intentionally conservative.

The protocol prioritizes:

- preventing hypoglycemia
- avoiding delayed interventions
- allowing human override
- avoiding runaway feeding loops

The system does **not attempt to perfectly model metabolism**.  
It simply ensures Benny receives carbohydrates if glucose becomes dangerous while unattended.