from dataclasses import dataclass
from drafter import *

OS_OPTIONS = ["Linux", "Windows Server", "Cisco IOS", "macOS", "UnifiOS", "OTHER"]
OS_FILTER_OPTIONS = ["All", "Linux", "Windows Server", "Cisco IOS", "macOS", "UnifiOS", "OTHER"]

@dataclass
class Host:
    hostname: str
    ip_address: str
    os_type: str
    open_port_count: int
    needs_patching: bool
    notes: str


@dataclass
class State:
    hosts: list[Host]
    admin_name: str
    selected_os_filter: str
    status_log: str
    maintenance_mode: bool

def make_navbar(state: State) -> list:
    nav_items = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
    ]
    if state.status_log != "":
        nav_items.append(bold("[System Log: " + state.status_log + "]"))
        nav_items.append("\n\n")
    return nav_items

@route
def index(state: State) -> Page:
    content = make_navbar(state)
    mode_text = "INACTIVE (Normal Operations)"
    if state.maintenance_mode:
        mode_text = "ACTIVE (Changes Restricted)"

    content.append(bold("Network Inventory Database"))
    content.append("\n")
    content.append("System Administrator: ")
    content.append(bold(state.admin_name))
    content.append("\nMaintenance Window: " + mode_text + "\n")
    content.append("Total hosts currently monitored: " + str(len(state.hosts)))

    return Page(state, content)

@route
def maintenance_page(state: State) -> Page:
    content = make_navbar(state)
    status_label = "DISABLED"
    if state.maintenance_mode:
        status_label = "ENABLED"

    content.append(bold("Maintenance Settings"))
    content.append("\n")
    content.append("Current Maintenance Status: ")
    content.append(bold(status_label))
    content.append("\n")
    content.append(Button("Toggle Maintenance Mode", toggle_maintenance))
    content.append("\n")
    content.append("--------------------------------------------------\n")
    content.append(bold("Administrator Settings\n"))
    content.append("System Administrator: " + state.admin_name + "\n")

    if state.maintenance_mode:
        content.append("Update Admin Operator Name: ")
        content.append(TextBox("new_admin", state.admin_name))
        content.append(Button("Update Name", update_admin))
    else:
        content.append(italic("Notice: Enable maintenance mode to change the admin name."))

    return Page(state, content)

@route
def update_admin(state: State, new_admin: str) -> Page:
    if new_admin == "":
        state.status_log = "Error: Admin operator name cannot be blank."
    else:
        state.admin_name = new_admin
        state.status_log = "Admin operator changed to: " + state.admin_name

    return maintenance_page(state)

@route
def toggle_maintenance(state: State) -> Page:
    if state.maintenance_mode:
        state.maintenance_mode = False
    else:
        state.maintenance_mode = True

    state.status_log = "Maintenance Mode is now set to: " + str(state.maintenance_mode)
    return maintenance_page(state)

@route
def host_roster(state: State) -> Page:
    content = make_navbar(state)
    content.append(bold("Network Host Roster"))
    content.append("\n")
    content.append("Filter by Operating System: ")
    content.append(SelectBox("os_filter", OS_FILTER_OPTIONS, state.selected_os_filter))
    content.append(Button("Apply OS Filter", apply_os_filter))
    content.append("\n")

    matched_devices = 0
    for host in state.hosts:
        if state.selected_os_filter == "All" or host.os_type == state.selected_os_filter:
            matched_devices = matched_devices + 1

            status_tag = "[Secured / Patched]"
            if host.needs_patching:
                status_tag = "[PATCH REQUIRED]"
            content.append(host.hostname + " (" + host.ip_address + ") | OS: " + host.os_type)
            content.append(" | Ports: " + str(host.open_port_count) + " | ")
            content.append(bold(status_tag))
            content.append("\n")
            content.append(italic("Notes: " + host.notes))
            content.append("\n")

    if matched_devices == 0:
        content.append("No hosts match the selected OS filter.\n")
        
    content.append("--------------------------------------------------\n")
    content.append(bold("Toggle Patch Status for a Host:\n"))
    content.append("Enter Exact Hostname: ")
    content.append(TextBox("target_hostname", ""))
    content.append(Button("Toggle Patch Status", toggle_patch_status))
    content.append("\n")

    return Page(state, content)

@route
def apply_os_filter(state: State, os_filter: str) -> Page:
    state.selected_os_filter = os_filter
    state.status_log = "Host filter set to: " + os_filter
    return host_roster(state)

@route
def toggle_patch_status(state: State, target_hostname: str) -> Page:
    found = False
    for host in state.hosts:
        if host.hostname == target_hostname:
            found = True
            if host.needs_patching:
                host.needs_patching = False
            else:
                host.needs_patching = True
            state.status_log = "Toggled patch status for: " + host.hostname
    if not found:
        state.status_log = "Error: Could not find host with hostname '" + target_hostname + "'."

    return host_roster(state)

@route
def provision_host_page(state: State) -> Page:
    content = make_navbar(state)
    content.append(bold("Provision New Network Asset"))
    content.append("\n")
    content.append("Hostname:\n")
    content.append(TextBox("hostname", "srv-new-01"))
    content.append("\nIP Address:\n")
    content.append(TextBox("ip_address", "192.168.1.50"))
    content.append("\nOperating System:\n")
    content.append(SelectBox("os_type", OS_OPTIONS, OS_OPTIONS[0]))
    content.append("\nOpen Port Count (Estimated):\n")
    content.append(TextBox("port_count_str", "2"))
    content.append("\nNeeds Patch: ")
    content.append(CheckBox("needs_patching", False))
    content.append("\nRunning Services & Notes:\n")
    content.append(TextArea("notes", "SSH (22), Web Server (80)"))
    content.append("\n")
    content.append(Button("Provision Host", save_new_host))

    return Page(state, content)

@route
def save_new_host(state: State, hostname: str, ip_address: str, os_type: str, port_count_str: str, needs_patching: bool, notes: str) -> Page:
    if hostname == "" or ip_address == "":
        state.status_log = "Error: Hostname and IP Address cannot be blank!"
        return provision_host_page(state)
    for host in state.hosts:
        if host.ip_address == ip_address:
            state.status_log = "Error: IP address " + ip_address + " is already assigned to " + host.hostname + "!"
            return provision_host_page(state)
        if host.hostname == hostname:
            state.status_log = "Error: hostname " + hostname + " is already assigned!"
            return provision_host_page(state)
    ports = int(port_count_str)

    new_host = Host(
        hostname,
        ip_address,
        os_type,
        ports,
        needs_patching,
        notes,
    )

    state.hosts.append(new_host)
    state.status_log = "Successfully provisioned host: " + hostname
    return host_roster(state)

@route
def vulnerability_audit(state: State) -> Page:
    content = make_navbar(state)
    total_hosts = len(state.hosts)
    total_ports = 0
    unpatched_count = 0
    high_risk_count = 0
    for host in state.hosts:
        total_ports = total_ports + host.open_port_count
        if host.needs_patching:
            unpatched_count = unpatched_count + 1
        if host.needs_patching and host.open_port_count > 3:
            high_risk_count = high_risk_count + 1

    content.append(bold("Network Vulnerability Audit"))
    content.append("\n")
    content.append("- Monitored Assets: " + str(total_hosts) + "\n")
    content.append("- Total Exposed Open Ports: " + str(total_ports) + "\n")
    content.append("- Unpatched Assets: " + str(unpatched_count) + "\n")
    content.append("- High-Risk Devices (Unpatched and >3 Open Ports): ")
    content.append(bold(str(high_risk_count)))
    content.append("\n")

    return Page(state, content)

initial_state = State(
    [],
    "Admin",
    "All",
    "System initialized.",
    False,
)

start_server(initial_state)



