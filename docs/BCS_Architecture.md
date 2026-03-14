# Benny Care System Architecture and Pinout

This document records the electrical mapping between the Raspberry Pi, driver boards, sensors, actuators, and power rails.  
The goal is to make the system understandable even when the hardware is completely disassembled.

Fields marked `[VERIFY]` should be confirmed during reassembly.

***

## Raspberry Pi Pin Usage Summary

| Physical Pin | Type | GPIO | Signal / Role | Destination |
|---------------|------|------|---------------|-------------|
| 4 | 5V | — | Logic VCC | BTS7960 H-Bridge |
| 6 | GND | — | Logic Ground | BTS7960 H-Bridge |
| 9 | GND | — | Ground | MOSFET Driver (Kibble) |
| 12 | PWM | GPIO18 | HONEY_FWD_PWM | H-Bridge Forward PWM |
| 16 | GPIO | GPIO23 | HONEY_FWD_EN | H-Bridge Forward Enable |
| 18 | GPIO | GPIO24 | KIBBLE_FEEDBACK | Spring Feedback Switch |
| 22 | GPIO | GPIO25 | KIBBLE_GATE | MOSFET Trigger |
| 35 | PWM | GPIO19 | HONEY_REV_PWM | H-Bridge Reverse PWM |
| 37 | GPIO | GPIO26 | HONEY_REV_EN | H-Bridge Reverse Enable |
| 14 | GND | — | Ground | Kibble Feedback Return |

### Reserved / Occupied Pin Notes

Pins currently occupied by BCS wiring:

4, 6, 9, 12, 14, 16, 18, 22, 35, 37

Remaining GPIO pins are available for future expansion.

Example possible future devices:

- cookie box servo
- status LED
- audible alert buzzer
- flow / position sensor

### Kibble Drop System

GPIO: 25  
Physical Pin: 22  
Function: Kibble Gate Trigger  
Wire Color: GREEN  
Driver Device: MOSFET gate  
Driver Board Location: TRIG/PWM header on MOSFET driver  
Physical Destination: Kibble pinwheel motor control MOSFET  

Associated Ground:  
Black wire → suggested Pi ground **Pin 9** `[VERIFY not already used]`

Notes:  
Ground must be common with MOSFET module ground.

***

GPIO: 24  
Physical Pin: 18  
Function: Kibble Feedback Sensor  
Wire Color: GREEN  

Device: Mechanical feedback switch  
Sensor Location: Spring module attached to kibble pinwheel mechanism  

Signal Meaning:  
Signal fires when spring compresses **or releases**  
(two transitions per mechanical cycle)

Associated Ground:  
Blue dupont → black insulated wire → suggested Pi ground **Pin 14** `[VERIFY not already used]`

***

### Honey Actuator (H-Bridge Control)

These signals control the H-bridge driving the honey syringe linear actuator.

GPIO: 18  
Physical Pin: 12  
Signal Name: HONEY_FWD_PWM  
Function: Forward PWM control  
Wire Color: YELLOW  
Destination: H-Bridge forward PWM input  

***

GPIO: 19  
Physical Pin: 35  
Signal Name: HONEY_REV_PWM  
Function: Reverse PWM control  
Wire Color: WHITE  
Destination: H-Bridge reverse PWM input  

***

GPIO: 23  
Physical Pin: 16  
Signal Name: HONEY_FWD_EN  
Function: Enable forward direction  
Wire Color: GREEN  
Destination: H-Bridge forward enable  

***

GPIO: 26  
Physical Pin: 37  
Signal Name: HONEY_REV_EN  
Function: Enable reverse direction  
Wire Color: GREEN  
Destination: H-Bridge reverse enable  

***

### H-Bridge Additional Connections

Driver Board Model: **BTS7960**

Logic Power:

H-Bridge Logic VCC → Raspberry Pi **Pin 4 (5V)**  
Wire Color: TEAL  

H-Bridge Logic GND → Raspberry Pi **Pin 6 (GND)**  
Wire Color: BLUE  

Motor Power:

Bridge Power Input  
B+ / B− ← from **12V power supply**

Motor Output:

M+ / M− → directly to **linear actuator**

***

## Raspberry Pi Power Connections

### Pi Power Supply

Power Source: USB-C power adapter  
Voltage: 5V  
Current Rating: **3.5A**

Connector System Used Elsewhere:

CENTROPOWER DC barrel plug connectors  
5.5 mm × 2.1 mm male/female adapters  
Used for modular 12V wiring.

***

### 5V Rail

Source: stock USB power supply included with the autofeeder.

Usage: powers kibble electronics and logic components.

Devices connected:

- kibble motor control board  
- MOSFET trigger module  

Connector Type: direct wiring from feeder supply.

Ground Reference:  
Must share common ground with Raspberry Pi `[VERIFY continuity]`.

***

### 12V Rail

Source: 12V 5A AC → DC power adapter  
120V AC → 12V DC converter  

Connector Type:  
5.5 mm × 2.1 mm DC barrel connectors  
(CENTROPOWER adapters)

Devices powered:

- honey linear actuator  
- BTS7960 H-bridge motor power input  

Ground Reference:

12V supply ground must connect to system ground  
so the Pi control signals share reference `[VERIFY]`.

***

## Actuator System

Device: Honey Syringe Linear Actuator

Specification:

- 12V actuator  
- 200 mm stroke (8")  
- ~1000 N / 220 lb force  
- ~0.47 in/sec travel speed

Power Source:

12V rail

Driver Board:

BTS7960 H-bridge motor driver

Control Signals:

- HONEY_FWD_PWM  
- HONEY_REV_PWM  
- HONEY_FWD_EN  
- HONEY_REV_EN  

Motor Outputs:

H-Bridge OUT1 → actuator lead A  
H-Bridge OUT2 → actuator lead B  

Mechanical Load:

Syringe plunger used for honey delivery.

Mounting Method:

Currently zip-tied to a thin plywood board.  
**Mechanical mount redesign is a high-priority improvement.**

***

## Kibble Drop Pinwheel Motor

Device: Pinwheel kibble dispenser motor.

Power Source:

5V rail from the autofeeder power supply.

Driver Board:

MOSFET trigger module  
MTDELE MOSFET switch driver  

Specifications:

- 5V–36V control  
- up to 15A continuous (30A peak)  
- supports PWM control

Control Signal:

GPIO 25 → MOSFET trigger input

Feedback Sensor:

GPIO 24

Sensor Type:

Mechanical spring tab contact.

A metal tab is bent by the rotating pinwheel  
and released by gaps in the wheel.

Feedback Meaning:

Spring compression or release event on the pinwheel  
(two electrical transitions per bin cycle).

***

## Ground Connections

The following grounds are part of the system ground network.

All power supplies and driver boards share a verified common ground reference.

### Raspberry Pi Ground Pins Used

Pin 6  
Used for: H-Bridge logic ground  
Wire Color: BLUE

Pin 9  
Used for: MOSFET driver ground (kibble motor control)  
Wire Color: BLACK  
[VERIFY this pin is not already occupied during final wiring]

Pin 14  
Used for: Kibble feedback sensor ground  
Wire: Blue dupont → black insulated wire  
[VERIFY final routing during reassembly]

### System Ground Domains

The following devices are tied into the common ground network:

• Raspberry Pi ground  
• MOSFET driver ground  
• BTS7960 logic ground  
• 12V actuator power supply ground  
• 5V autofeeder power supply ground

Common reference between supplies has been **verified with a multimeter**.
