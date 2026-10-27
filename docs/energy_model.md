# 3GPP State-Based Energy and Battery Lifetime Model

## 1. Theoretical Foundation

Power consumption in 5G cellular IoT devices (NB-IoT, LTE-M, and 5G RedCap) is governed by distinct radio frequency (RF) and baseband operational states. In accordance with **3GPP TR 38.840** (*Study on User Equipment (UE) power saving in NR*) and vendor hardware profiles (e.g., Nordic nRF9160, Qualcomm 315), the operational state space is modeled as a discrete-state Markovian power model:

$$\mathcal{S} = \{\text{DEEP\_SLEEP}, \text{PO\_MONITOR}, \text{ACTIVE\_RX}, \text{ACTIVE\_TX}, \text{INACTIVITY}\}$$

---

## 2. Power and Timing Parameters

| State | Symbol | Power (mW) | Default Duration | Functional Description |
|---|---|---|---|---|
| **Deep Sleep** | $P_{sleep}$ | $0.015\text{ mW}$ ($15\ \mu\text{W}$) | Variable | RF synthesizer and baseband off. Only 32 kHz RTC running. |
| **PO Monitoring** | $P_{listen}$ | $45.0\text{ mW}$ | $15\text{ ms}$ | RF synthesizer warm-up, AGC, blind decoding of PDCCH with P-RNTI. |
| **Active RX** | $P_{rx}$ | $110.0\text{ mW}$ | $60\text{ ms}$ | Demodulation and decoding of PDSCH transport blocks and RRC messages. |
| **Active TX** | $P_{tx}$ | $320.0\text{ mW}$ | $40\text{ ms}$ | Uplink RACH preamble transmission, PUCCH ACK/NACK (23 dBm PA). |
| **Inactivity** | $P_{inact}$ | $45.0\text{ mW}$ | $100\text{ ms}$ | Baseband monitors PDCCH for contiguous downlink transfers before sleep. |

---

## 3. Mathematical Equations

### 3.1 Energy Integration
For a device $i$ across $K$ state transitions during simulation horizon $T_{sim}$:

$$E_{total, i} = \sum_{k=1}^{K} P(s_k) \cdot \Delta t_k \quad [\text{Joules}]$$

where $P(s_k)$ is the power in Watts for state $s_k$, and $\Delta t_k$ is the dwell time in seconds.

### 3.2 Battery Energy Capacity
For a nominal lithium thionyl chloride ($\text{Li-SOCl}_2$) or lithium-ion cell with nominal voltage $V_{cell}$ and rated capacity $Q_{mAh}$:

$$E_{battery} = V_{cell} \times \left(\frac{Q_{mAh}}{1000}\right) \times 3600 \quad [\text{Joules}]$$

For our default parameters ($V_{cell} = 3.0\text{ V}$, $Q_{mAh} = 1200\text{ mAh}$):
$$E_{battery} = 3.0 \times 1.2 \times 3600 = 12,960\text{ Joules}$$

### 3.3 Modeled Operational Lifetime
Given the average estimated power draw $\overline{P}_{avg} = \frac{E_{total, i}}{T_{sim}}$:

$$\text{Lifetime (seconds)} = \frac{E_{battery}}{\overline{P}_{avg}}$$

$$\text{Lifetime (years)} = \frac{\text{Lifetime (seconds)}}{3600 \times 24 \times 365.25}$$

---

## 4. Disclaimers and Labeling Notice

> [!IMPORTANT]
> **Academic Rigor Notice:** All energy metrics and battery life estimates reported in this simulation are **modeled values** derived from calibrated mathematical state models and 3GPP specifications. They do not represent empirical measurements from physical hardware test benches. Hardware power is labeled throughout this codebase as **Estimated Modeled Energy**.

