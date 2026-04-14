
# Multi-Switch Flow Table Analyzer using POX

## 👨‍🎓 Student Details

**Name:** Shibi Shetty
**SRN:** PES2UG24CS467

---

# 🎯 Problem Statement

Design and implement an SDN-based system that analyzes flow tables across multiple switches and identifies **ACTIVE** and **UNUSED** flows using OpenFlow.

---

# 🛠 Tools Required

* Mininet
* POX Controller
* Python (comes with POX)
* Terminal (WSL / Ubuntu)

---

# 🧠 Basic Idea (VERY SIMPLE)

* Switch doesn’t know where to send packet → asks controller
* Controller decides → installs rule
* We track:

  * Packets
  * Bytes
  * Flow usage

---

# 🖥️ IMPORTANT: TERMINAL SETUP

👉 You MUST use **2 terminals**

### 🟢 Terminal 1 → Controller (POX)

### 🔵 Terminal 2 → Mininet

---

# 🚀 STEP-BY-STEP EXECUTION (FOLLOW EXACTLY)

---

## 🔹 STEP 0: Clean Old Network

👉 Terminal 2:


sudo mn -c


## 🔹 STEP 1: Start Controller

👉 Terminal 1:

cd ~/pox
./pox.py misc.flow_analyzer


📸 Screenshot 1: Controller Started
<img width="1920" height="1080" alt="Screenshot 2026-04-10 123919" src="https://github.com/user-attachments/assets/bb40a630-9b47-4603-91af-8ca58d2af144" />


## 🔹 STEP 2: Start Mininet

👉 Open Terminal 2:


sudo mn --topo linear,3 --controller remote


📸 Screenshot 2: Topology
<img width="1920" height="448" alt="Screenshot 2026-04-10 125557" src="https://github.com/user-attachments/assets/ae38c418-12ba-4b73-97a2-f671b0084655" />

---

## 🔹 STEP 3: Test Connectivity

👉 Inside Mininet:


pingall


📸 Screenshot 3: Ping (0% dropped)

<img width="1920" height="377" alt="Screenshot 2026-04-10 124207" src="https://github.com/user-attachments/assets/212c0c97-d4ec-4605-9663-3dff399a396a" />


## 🔹 STEP 4: Start iperf Server


h3 iperf -s &


📸 Screenshot 4: iperf server

<img width="1920" height="377" alt="Screenshot 2026-04-10 124207" src="https://github.com/user-attachments/assets/a6b27206-5012-4d43-b6ab-5585b7373d05" />


## 🔹 STEP 5: Run iperf Client


h1 iperf -c h3


📸 Screenshot 5: iperf output (bandwidth)

<img width="1920" height="377" alt="Screenshot 2026-04-10 124207" src="https://github.com/user-attachments/assets/1a7cc174-49c5-49c0-96ad-f3f489259ce6" />


## 🔹 STEP 6: Check Controller Logs

👉 Go to Terminal 1

📸 Screenshot 6: Multi-switch logs
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/f975dc90-dbf0-47b7-a390-2b9e390e8afa" />

📸 Screenshot 7: Flow details (Packets, Bytes, Status)
<img width="1920" height="1080" alt="image" src="https://github.com/user-attachments/assets/062f72df-a9a7-47ab-bb8d-7f0f94c39ce5" />

---

# 📊 What You Should See

Example:

```
Packets: 406063
Bytes: 18137216758
Status: ACTIVE
```

---

# 📸 FINAL SCREENSHOT ORDER

1. Controller Start
2. Topology
3. Ping
4. iperf Server
5. iperf Output
6. Multi-switch Logs
7. Flow Details

---

# 🧾 FULL PYTHON CODE (flow_analyzer.py)

```python
from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()
mac_to_port = {}

def _handle_ConnectionUp(event):
    log.info("Switch %s connected", event.dpid)

def _handle_PacketIn(event):
    packet = event.parsed

    if not packet.parsed:
        return

    dpid = event.dpid
    in_port = event.port

    src = packet.src
    dst = packet.dst

    mac_to_port.setdefault(dpid, {})
    mac_to_port[dpid][src] = in_port

    if dst in mac_to_port[dpid]:
        out_port = mac_to_port[dpid][dst]
    else:
        out_port = of.OFPP_FLOOD

    actions = [of.ofp_action_output(port=out_port)]

    if out_port != of.OFPP_FLOOD:
        match = of.ofp_match.from_packet(packet, in_port)

        flow_mod = of.ofp_flow_mod()
        flow_mod.match = match
        flow_mod.actions = actions
        flow_mod.idle_timeout = 10

        event.connection.send(flow_mod)

    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions = actions
    msg.in_port = in_port

    event.connection.send(msg)

def _handle_FlowStatsReceived(event):
    log.info("---- Flow Stats from Switch %s ----", event.connection.dpid)

    for stat in event.stats:
        if stat.priority == 0:
            continue

        if stat.packet_count > 0:
            status = "ACTIVE"
        else:
            status = "UNUSED"

        log.info("Packets: %d Bytes: %d Status: %s",
                 stat.packet_count, stat.byte_count, status)

def _request_stats():
    for connection in core.openflow._connections.values():
        connection.send(of.ofp_stats_request(body=of.ofp_flow_stats_request()))

def launch():
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    core.openflow.addListenerByName("FlowStatsReceived", _handle_FlowStatsReceived)

    from pox.lib.recoco import Timer
    Timer(5, _request_stats, recurring=True)

    log.info("Flow Analyzer Controller Started")
```

---



# ✅ CONCLUSION

* Multi-switch network created
* Controller installs flow rules
* Traffic generated using iperf
* Flow stats collected
* Active flows identified



---
