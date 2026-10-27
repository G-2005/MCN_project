# 5G Adaptive Paging Architecture Specification

## 1. System Overview

In cellular 5G New Radio (NR) networks, massive Machine-Type Communications (mMTC) and Reduced Capability (RedCap) IoT devices spend the vast majority of their operational lifetimes in ultra-low-power sleep states (`RRC_IDLE` or `RRC_INACTIVE`). When downlink traffic arrives from external application servers or the 5G Core (5GC), the network must page the device to trigger an RRC connection setup before user-plane data can be transferred.

Standard 3GPP Discontinuous Reception (DRX) and extended DRX (eDRX) mechanisms utilize fixed periodic Paging Occasions (POs). This incurs an unavoidable engineering trade-off:
- **Short DRX cycles** (e.g., 1.28s) deliver packets with low latency, but subject the device to hundreds of empty wake-up events, depleting the battery through repeated RF synthesizer warm-ups and PDCCH blind decoding.
- **Long eDRX cycles** (e.g., 5.12s, 10.24s) conserve battery power during quiescent intervals, but introduce intolerable delivery latency and cause catastrophic packet deadline violations during sudden traffic bursts.

**AdaPaging** resolves this dilemma by dynamically adjusting the wake-up interval $T_{wake}(t)$ in response to observed traffic dynamics, QoS latency budgets ($D_{max}$), and strict configurable bounds.

---

## 2. Component Architecture

```
+-----------------------------------------------------------------------------------+
|                                  5G CORE (5GC)                                    |
|   +-----------------------+   +-----------------------+   +-------------------+   |
|   | UPF (User Plane)      |   | AMF (Access & Mobility|   | SMF (Session Mgmt)|   |
|   | Downlink Data Arrival |   | Paging Request Gen    |   | QoS Flow & Deadlines  |
+---+-----------+-----------+---+-----------+-----------+---+---------+---------+---+
                |                           |                         |
                +---------------------------+-------------------------+
                                            | N2/N3 Interface
                                            v
+-----------------------------------------------------------------------------------+
|                            5G gNodeB / BASE STATION                               |
|  +-----------------------------------------------------------------------------+  |
|  |                     Adaptive Paging Controller (AdaPaging)                  |  |
|  |  * Per-UE Downlink Priority Buffers                                         |  |
|  |  * EWMA Inter-Arrival Tracker: \hat{\tau}_k = \alpha \Delta t + (1-\alpha)\hat{\tau} |
|  |  * QoS Latency Clamping: T_{upper} = min(T_{max}, \beta \cdot D_{max})       |  |
|  |  * Multiplicative Idle Backoff: T_{next} = min(T_{upper}, T \cdot (1+\gamma))|  |
|  |  * Burst Contraction: T_{next} = max(T_{min}, min(T_{burst}, 0.5 \hat{\tau})) |  |
|  +--------------------------------------+--------------------------------------+  |
|                                         |                                         |
|  +--------------------------------------v--------------------------------------+  |
|  |                     Paging Channel (PCH) Scheduler                          |  |
|  |  * Physical Paging Occasion (PO) Calculation                                 |  |
|  |  * Paging Record Bundling (up to 16 UEs per PDSCH transport block)          |  |
|  |  * Elimination of Blind Broadcast Storms                                    |  |
|  +-----------------------------------------------------------------------------+  |
+-------------------------------------------+---------------------------------------+
                                            | Over-The-Air (Uu Air Interface)
                       +--------------------+--------------------+
                       | PDCCH (P-RNTI)                          | PDSCH Downlink Data
                       v                                         v
+-----------------------------------------------------------------------------------+
|                        SLEEPING IoT DEVICE POPULATION (UEs)                       |
|                                                                                   |
|  [State: DEEP_SLEEP]        [State: PO_MONITOR]           [State: ACTIVE_RX/TX]   |
|  P_sleep = 15 uW            P_listen = 45 mW              P_rx = 110 mW           |
|  Baseband & RF Off          PDCCH Blind Decode (15ms)     P_tx = 320 mW           |
|  Sleeps up to T_upper       Adapts T_wake dynamically     RACH + Data Reception   |
+-----------------------------------------------------------------------------------+
```

---

## 3. Discrete-Event Simulation Engine

The simulation is built on a high-performance continuous-time priority-queue discrete-event engine (`src/core/event_engine.py`) using Python's `heapq`:

1. **Deterministic Ordering**: Event tuples `(timestamp, event_id, event_type, payload)` guarantee microsecond-fidelity event resolution and prevent state-dependent nondeterminism.
2. **Event Types**:
   - `PACKET_ARRIVE`: Downlink packet reaches gNodeB from core network.
   - `UE_WAKEUP`: UE transitions from `DEEP_SLEEP` to `PO_MONITOR` at its assigned PO.
   - `PAGING_TRANSMIT`: gNodeB broadcasts physical paging frame over PDCCH.
   - `DATA_DELIVER`: Uplink RACH handshake and downlink PDSCH transfer complete.
   - `INACTIVITY_EXPIRE`: RRC inactivity timer finishes, allowing the UE to return to deep sleep.
3. **Trace Preservation**: For any given random seed, the synthesized traffic trace is created once and fed identically to both baseline and proposed algorithms, ensuring perfect experimental fairness.

---

## 4. Synchronization Mechanism

A common concern in adaptive paging is how the gNodeB and the sleeping UE remain synchronized regarding the device's wake-up timing without constant over-the-air signaling:

1. **Deterministic State Machine**: Both the gNodeB Paging Controller and the IoT UE execute the identical deterministic AdaPaging recurrence relation.
2. **Deterministic Inputs**:
   - Both sides observe the exact same packet reception events (via RRC data transfers and MAC ACKs).
   - Both sides maintain the same idle wake-up counter $N_{idle}$.
   - The QoS latency budget $D_{max}$ is negotiated once during initial PDU session establishment (or RRC Connection Setup) and stored in the UE context.
3. **Drift Immunity**: Because clock drift in modern 3GPP temperature-compensated crystal oscillators (TCXO) is under $\pm 2$ ppm, the 15 ms PO monitoring window provides ample guard band for wake-up synchronization over multi-second sleep intervals.

