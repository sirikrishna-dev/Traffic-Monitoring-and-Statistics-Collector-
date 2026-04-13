# Traffic Monitoring and Statistics Collector
**Course:** UE24CS252B — Computer Networks
**SDN Framework:** Ryu Controller + Mininet
**OpenFlow Version:** 1.3

## Problem Statement
Build a controller module that collects and displays traffic statistics:
- Retrieve flow statistics from OpenFlow switches
- Display packet/byte counts per flow
- Periodic monitoring (every 10 seconds)
- Generate simple traffic reports saved to file

## Topology
```
     h1 (10.0.0.1)
      \
h3 -- s1 -- h2     (10.0.0.2, 10.0.0.3)
      |
      s2
     / \
   h4   h5         (10.0.0.4, 10.0.0.5)
```
2 switches, 5 hosts connected via OpenFlow

## Setup & Execution

### Prerequisites
- Ubuntu 20.04/22.04 (VirtualBox VM)
- Mininet: `sudo apt install mininet -y`
- Ryu: `pip install ryu`

### Step 1 — Start Ryu Controller (Terminal 1)
```
ryu-manager traffic_monitor.py
```

### Step 2 — Start Mininet Topology (Terminal 2)
```
sudo python3 custom_topology.py
```

### Step 3 — Test in Mininet CLI
```
pingall
iperf h1 h2
h1 ping -c 10 h2
sh ovs-ofctl dump-flows s1
sh ovs-ofctl dump-flows s2
```

## Test Scenarios

### Scenario 1 — Normal Traffic
- All 5 hosts ping each other: 0% packet loss (20/20 received)
- iperf h1 to h2: ~28-33 Gbits/sec
- iperf h3 to h5: ~21 Gbits/sec

### Scenario 2 — Flow Table Verification
- Before traffic: 0 flow entries
- After traffic: 18 flow entries with match fields
- Packet/byte counts visible in periodic TRAFFIC REPORT

## Expected Output
```
TRAFFIC REPORT  |  Switch: 1  |  2026-04-11 21:43:36
Priority   Match                  Packets    Bytes
1          OFPMatch(in_port=1)          2      196
Total flow entries shown: 18
```
Reports are also saved to traffic_report.txt

## Files
| File | Description |
|------|-------------|
| traffic_monitor.py | Ryu controller with flow monitoring |
| custom_topology.py | Mininet topology (2 switches, 5 hosts) |
| traffic_report.txt | Auto-generated traffic report |

## References
1. Ryu SDN Framework - https://ryu.readthedocs.io/
2. Mininet - https://mininet.org/
3. OpenFlow 1.3 Spec - https://opennetworking.org/
```

---

