
autoprotocol modes and behaviors - these would be a pretty big help This would probably be a big deal for like my mental health, for Benny's care while I'm gone, his long-term care honestly, it would probably make better decisions than I would after just just I don't know a handful of refinements...

   1. Leaving Benny at Home (Mode)
   2. Benny and I are not at Home (Mode)
   3. I'm home (Mode)
   4. Recording Injections
   5. Recording Activity
   6. Recording Food
   7. A sophisticated auto-protocol that gives *me* decent advice when it's not in charge and does fine when it *is* in charge.
   8. Test the auto-protocol against a live stream
   9. rewiring/housing the wires for the BCS in such a way that they're like, safer, won't be pulled, etc.
   10. Maybe mounting *everything* on a common board/box so it's tidier/safer
   11. Rethinking the system knowing we need a human on call
   12. Using the system to dispense the food I feed him anyway
       1. e.g. putting it up higher most of the time.
   13. I can't really do the cookie box because I don't know how to mount it so the dogs won't fuck it up
   14. Massive Watch software update
   15. New Functions
   16. New Interface
         1. (descending tiles)
   17. Snapshot Debugging
         1. Looks like the hook doesn't run !snapshot it runs snapshot which doesn't do anything anymore
         2. It also is happy to send me an old snapshot instead of indicating failure.
            1. so there's a silent failure with old snapshot.
            2. That's bad.
   18. Test whether home internet continues running during power outage on UPS
   19. Buy longer-running uninterruptible PSU
   20. Camera detecting successful dispensation
   21. Camera detecting consumption
   22. BCS Human Contingincies
   23. More BCS backup/failure modes
   24. Get a much larger housing box and a standoff/mounting kit
   25. Things kinda need to be routed around the basic assumption that there's a human on call
   26. Also - How do I get a human on call?
Light so you can see better from the camera

   Okay cool, what does benny need rn -
   well there's the bcs
   there's finding someone to watch him/be on call about him.
   there's... huh. Idk what else there is.
   Oh finding a job where Benny can be (that's kinda tricky!)
   idk some comfort type stuff. like maybe we could get a softer mat to stick outside in the sun or...
   Yeah this is all a little more comprehensive.

# Next

- Update Service

```bash
sudo cp bennycareserver.service /etc/systemd/system
```

- Enable and start

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bennycareserver.service
```

- logs and status

```bash
systemctl status bennycareserver.service
journalctl -u bennycareserver.service -f
```

1) Edit the unit file
sudo nano /etc/systemd/system/bennycareserver.service

2) Tell systemd to re-read unit files
sudo systemctl daemon-reload

3) Restart the service
sudo systemctl restart bennycareserver.service

4) Check status + logs
systemctl status bennycareserver.service --no-pager
journalctl -u bennycareserver.service -n 60 --no-pager

## Ideas

1. Honey Feeder
2. Designing Honey Feeder
3. Building Honey Feeder
4. Testing Honey Feeder
5. Failure Points Honey Feeder
6. Redundancies Honey FeederKibble Feeder
7. Designing Kibble Feeder
8. Building Kibble Feeder
9. Testing Kibble Feeder
10. Failure Points Kibble Feeder
11. Redundancies Kibble FeederCamera Mount
12. Designing Camera Mount
13. Building Camera Mount
14. Testing Camera Mount
15. Failure Points Camera Mount
16. Redundancies Camera MountFeeding Chime
17. Designing Feeding Chime
18. Building Feeding Chime
19. Testing Feeding Chime
20. Failure Points Feeding Chime
21. Redundancies Feeding ChimeLibre Graph
22. Designing Libre Graph
23. Building Libre Graph
24. Testing Libre Graph
25. Failure Points Libre Graph
26. Redundancies Libre GraphRedundant Data Access
27. Designing Redundant Data Access
28. Building Redundant Data Access
29. Testing Redundant Data Access
30. Failure Points Redundant Data Access
31. Redundancies Redundant Data AccessRedundant Control Access
32. Designing Redundant Control Access
33. Building Redundant Control Access
34. Testing Redundant Control Access
35. Failure Points Redundant Control Access
36. Redundancies Redundant Control AccessRedundant Monitoring Access
37. Designing Redundant Monitoring Access
38. Building Redundant Monitoring Access
39. Testing Redundant Monitoring Access
40. Failure Points Redundant Monitoring Acces
41. Redundancies Redundant Monitoring AccessHomelab
42. Designing Homelab
43. Building Homelab
44. Testing Homelab
45. Failure Points Homelab
46. Redundancies HomelabLibre
47. Failure Points Libre
48. Redundancies LibreComponent Audit
49. List all Components
50. Fail Check Each Component
51. Redundancy / Backup / Manual Backup for each component failurePotential Failures
52. ISP Failure
53. Router/Modem Failure
54. Server Failure
55. Phone Failure
56. Redundant Bluetooth Libre to Server Connection
57. Libre Fails or is removed
58. Benny doesn't wake up
59. Mechanical Failure on Dispensation
60. Power OUtage
61. Default Rescue Mode
62. Regardless of what fails or how, default to feeding food/rescue reiably.
63. Need Camera to Veify it's ***Benny*** who eats his foo
64. Dogs get into food early
65. PI Compatibility Check
66. Make sure the project is still capable of running on pi + pi venv cleanup
67. SSH Disconnect Issue with PI
68. Plug Camera into PI
69. Write something to see camera images from P
70. PI Camera Testing
71. Let's look at the dev.md for testing and redundancy criteria - should help other projects as well
72. Fix up this Document

### Server Driver

23

### Honey Drop Rescue

Server Brains, Server Driver ~ 18

### Verification station (camera)

Server Brains and Driver - 10

### Kibble Autofeeder Bowl

10

### Deadman's Switch and Watchdog Circuit Redundancies

Honey Drop ~ 8

### Honey drop rescue alert

7

### Kibble Autofeeder Alert

7

### Kibble Autofeeder Serving Mechanism

Brains, Driver, Bowl ~6

### Training process

Alerts ~ 6

### Server LLU Subversion BLE Direct Hack

4

Okay so there's ants

Need anything that touches food to be washable

Everything should be unpluggable. like nothing should be hardwired to anything UNLESS they NEVER need to be disconnected AND they're physically mounted together... which.. is not a terrible idea honestly.

I should get those crimpy cold weld airless things for my wires

Maybe integrating the pre-check into discord or whatever service we interact with - just like "set up" and then we go through a process saying "done" and then checking that it works, etc.

Okay other gripes

- record keeping is important
- This thing should be prioritized
- I could really use a backpack for benny
- Bike with a basket on the front for Benny
- BCS is really scary and unpleasant to work on
- I mean, maybe we try to think of a more integrative BCS, right?
- What else - toenail trimming is really hard
- Oh I wish we had a better rug
- The phone overheated
- It's really inconvenient leaving my cellphone at home - we could avoid 90% of the issues with the watch by simply getting another phone to leave with him
- (costs money though)
- Obviously the bluetooth pi reader is a good idea as well.
- redundancy checking
- failures I haven't thought of


I definitely wouldn't mind more of an operator seat as like a phone app. 

oh I think I need like LED indicators for most of the electrical paths if that's possible. because like it would just be a lot easier to check shit like that right?