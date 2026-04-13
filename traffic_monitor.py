from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet
from ryu.lib import hub
import time
import datetime

class TrafficMonitor(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficMonitor, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)
        self.report_data = []

    # ── Switch connects ──────────────────────────────────────────
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser
        self.datapaths[datapath.id] = datapath
        self.logger.info("Switch connected: dpid=%s", datapath.id)

        # Default rule: send unknown packets to controller
        match  = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, idle=0, hard=0):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(
                    ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            idle_timeout=idle, hard_timeout=hard,
            match=match, instructions=inst)
        datapath.send_msg(mod)

    # ── Learning switch logic ────────────────────────────────────
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg      = ev.msg
        datapath = msg.datapath
        ofproto  = datapath.ofproto
        parser   = datapath.ofproto_parser
        in_port  = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst, src = eth.dst, eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        out_port = (self.mac_to_port[dpid][dst]
                    if dst in self.mac_to_port[dpid]
                    else ofproto.OFPP_FLOOD)

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self.add_flow(datapath, 1, match, actions, idle=10, hard=30)

        out = parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=msg.data if msg.buffer_id == ofproto.OFP_NO_BUFFER else None)
        datapath.send_msg(out)

    # ── Periodic stats request (every 10 seconds) ────────────────
    def _monitor(self):
        while True:
            for dp in list(self.datapaths.values()):
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        parser = datapath.ofproto_parser
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)

    # ── Receive and display stats ────────────────────────────────
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def flow_stats_reply_handler(self, ev):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        dpid = ev.msg.datapath.id

        print("\n" + "="*60)
        print(f"  TRAFFIC REPORT  |  Switch: {dpid}  |  {timestamp}")
        print("="*60)
        print(f"{'Priority':<10} {'Match':<30} {'Packets':>10} {'Bytes':>12}")
        print("-"*60)

        for stat in ev.msg.body:
            if stat.priority == 0:          # skip table-miss entry
                continue
            entry = {
                "time":     timestamp,
                "dpid":     dpid,
                "priority": stat.priority,
                "match":    str(stat.match),
                "packets":  stat.packet_count,
                "bytes":    stat.byte_count,
            }
            self.report_data.append(entry)

            print(f"{stat.priority:<10} "
                  f"{str(stat.match):<30} "
                  f"{stat.packet_count:>10} "
                  f"{stat.byte_count:>12}")

        print("-"*60)
        print(f"  Total flow entries shown: {len(ev.msg.body)-1}")
        print("="*60 + "\n")

        # Save report to file
        self._save_report(timestamp, dpid, ev.msg.body)

    def _save_report(self, timestamp, dpid, body):
        with open("traffic_report.txt", "a") as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Switch: {dpid} | Time: {timestamp}\n")
            f.write(f"{'Priority':<10} {'Packets':>10} {'Bytes':>12}\n")
            f.write(f"{'-'*40}\n")
            for stat in body:
                if stat.priority == 0:
                    continue
                f.write(f"{stat.priority:<10} "
                        f"{stat.packet_count:>10} "
                        f"{stat.byte_count:>12}\n")
