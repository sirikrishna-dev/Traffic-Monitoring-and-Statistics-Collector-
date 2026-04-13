from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.topo import Topo
from mininet.log import setLogLevel
from mininet.cli import CLI

class MonitorTopo(Topo):
    """
    Topology:
         h1
          \
    h3 -- s1 -- h2
          |
          s2
         / \
       h4   h5
    """
    def build(self):
        # Switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')

        # Hosts on s1
        h1 = self.addHost('h1', ip='10.0.0.1/24')
        h2 = self.addHost('h2', ip='10.0.0.2/24')
        h3 = self.addHost('h3', ip='10.0.0.3/24')

        # Hosts on s2
        h4 = self.addHost('h4', ip='10.0.0.4/24')
        h5 = self.addHost('h5', ip='10.0.0.5/24')

        # Links
        self.addLink(h1, s1)
        self.addLink(h2, s1)
        self.addLink(h3, s1)
        self.addLink(s1, s2)
        self.addLink(h4, s2)
        self.addLink(h5, s2)

def run():
    setLogLevel('info')
    topo = MonitorTopo()
    net  = Mininet(topo=topo,
                   controller=RemoteController('c0', ip='127.0.0.1', port=6633),
                   switch=OVSSwitch)
    net.start()
    print("\n✅ Network started. Controller should be running separately.")
    print("   Try: pingall, iperf h1 h2, h1 ping h5\n")
    CLI(net)
    net.stop()

if __name__ == '__main__':
    run()
vboxuser@ubuntu:~/s