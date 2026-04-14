# Import core POX modules
from pox.core import core
import pox.openflow.libopenflow_01 as of

# Logger to print messages in terminal
log = core.getLogger()

# Dictionary to store MAC address to port mapping
# Format: {switch_id: {mac_address: port}}
mac_to_port = {}


# 🔹 Event: When a switch connects to controller
def _handle_ConnectionUp(event):
    log.info("Switch %s connected", event.dpid)


# 🔹 Event: When a packet arrives at switch and no rule exists
def _handle_PacketIn(event):
    
    # Parse the incoming packet
    packet = event.parsed

    # If packet is not valid, ignore
    if not packet.parsed:
        return

    # Get switch ID and incoming port
    dpid = event.dpid
    in_port = event.port

    # Get source and destination MAC addresses
    src = packet.src
    dst = packet.dst

    # Initialize dictionary for this switch if not present
    mac_to_port.setdefault(dpid, {})

    # Learn: Map source MAC to incoming port
    mac_to_port[dpid][src] = in_port

    # 🔹 Decide where to send the packet
    if dst in mac_to_port[dpid]:
        # If destination is known → send to that port
        out_port = mac_to_port[dpid][dst]
    else:
        # If unknown → flood to all ports
        out_port = of.OFPP_FLOOD

    # Define action (output to selected port)
    actions = [of.ofp_action_output(port=out_port)]

    # 🔹 Install flow rule ONLY if destination is known
    if out_port != of.OFPP_FLOOD:

        # Create match conditions from packet
        match = of.ofp_match.from_packet(packet, in_port)

        # Create flow rule
        flow_mod = of.ofp_flow_mod()
        flow_mod.match = match        # Matching fields
        flow_mod.actions = actions    # Action (forward)
        flow_mod.idle_timeout = 10    # Remove rule after 10 sec of inactivity

        # Send rule to switch
        event.connection.send(flow_mod)

    # 🔹 Send the current packet immediately
    msg = of.ofp_packet_out()
    msg.data = event.ofp
    msg.actions = actions
    msg.in_port = in_port

    event.connection.send(msg)


# 🔹 Event: When switch sends flow statistics
def _handle_FlowStatsReceived(event):

    # Print which switch stats are coming from
    log.info("---- Flow Stats from Switch %s ----", event.connection.dpid)

    # Loop through all flow entries
    for stat in event.stats:

        # Ignore default flow (priority 0)
        if stat.priority == 0:
            continue

        # 🔹 Classify flow
        if stat.packet_count > 0:
            status = "ACTIVE"
        else:
            status = "UNUSED"

        # Print flow statistics
        log.info(
            "Packets: %d | Bytes: %d | Status: %s",
            stat.packet_count,
            stat.byte_count,
            status
        )


# 🔹 Function to request flow stats from switches
def _request_stats():

    # Loop through all connected switches
    for connection in core.openflow._connections.values():

        # Send request for flow statistics
        connection.send(
            of.ofp_stats_request(
                body=of.ofp_flow_stats_request()
            )
        )


# 🔹 Launch function (entry point of controller)
def launch():

    # Register event listeners
    core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
    core.openflow.addListenerByName("PacketIn", _handle_PacketIn)
    core.openflow.addListenerByName("FlowStatsReceived", _handle_FlowStatsReceived)

    # Timer to request stats every 5 seconds
    from pox.lib.recoco import Timer
    Timer(5, _request_stats, recurring=True)

    log.info("Flow Analyzer Controller Started")
