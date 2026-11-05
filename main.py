from dataclasses import dataclass
from drafter import *

OS_OPTIONS = ["Linux", "Windows Server", "Cisco IOS", "macOS", "UnifiOS", "OTHER"]
OS_FILTER_OPTIONS = ["All", "Linux", "Windows Server", "Cisco IOS", "macOS", "UnifiOS", "OTHER"]
set_site_information(
    author="Seth",
    description="Network Inventory Database",
    links="https://github.com/cerbsys/network-asset-inventory/"
)
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
    '''
    creates the bar at the top of with all of the buttons.
    
    Args:
        state: State (the current state of the program)
    Returns:
        list: (list of all buttons)
    '''
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
    '''
    creates the first page, a dashboard
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page: (the dashboard page)
    '''
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
    '''
    creates maintenance page
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page (the updated maintenance page)
    '''
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
    '''
    updates the admin name
    
    Args:
        state: State (the current state of the program)
        new_admin: str (the updated name)
    Returns:
        Page (updated maintence page with new admin name)
    '''

    if new_admin == "":
        state.status_log = "Error: Admin operator name cannot be blank."
    else:
        state.admin_name = new_admin
        state.status_log = "Admin operator changed to: " + state.admin_name

    return maintenance_page(state)

@route
def toggle_maintenance(state: State) -> Page:
    '''
    turns on or off the maintenance mode, allows for admin change
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page (updated maintenance page)
    '''
    if state.maintenance_mode:
        state.maintenance_mode = False
    else:
        state.maintenance_mode = True

    state.status_log = "Maintenance Mode is now set to: " + str(state.maintenance_mode)
    return maintenance_page(state)

@route
def host_roster(state: State) -> Page:
    '''
    creates page with all provisioned hosts listed out.
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page (updated host roster page)
    '''
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
    '''
    sets the OS filter to whatever the user selected
    
    Args:
        state: State (the current state of the program)
        os_filter (the selected filter)
    Returns:
        Page: (updated host roster page with the filtered results)
    '''
    state.selected_os_filter = os_filter
    state.status_log = "Host filter set to: " + os_filter
    return host_roster(state)

@route
def toggle_patch_status(state: State, target_hostname: str) -> Page:
    '''
    sets a host to patched or unpatches
    
    Args:
        state: State (the current state of the program)
        target_hostname: str (the hostname of the chosen device)
    Returns:
        Page: (updated host roster page with the patch toggle applied)
    '''
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
    '''
    creates page for user to add hosts
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page: (page for user to add hosts)
    '''
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
    '''
    Args:
        state: State (the current state of the program)
        hostname (name of device)
        ip_address (ip of device)
        os_type (device operating system)
        port_count_str (number of open ports on the device)
        needs_patching (T or F of whether device needs patched)
        notes (anything the user wants to specify)
    Returns:
        Page (updated host roster with the new device)
    '''
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
    '''
    creates a new page called vulnerability audit
    
    Args:
        state: State (the current state of the program)
    Returns:
        Page: (updated audit page)
    '''
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


from drafter import assert_equal


# UNIT TESTS FOR ALL FUNCTIONS 
def test_make_navbar():
    state = State([], "Alice", "All", "Cache cleared", False)
    nav = make_navbar(state)

    expected = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("[System Log: Cache cleared]"),
        "\n\n",
    ]
    assert_equal(nav, expected)


def test_index():
    host = Host("web-01", "10.0.0.1", "Linux", 2, False, "Web server")
    state = State([host], "Bob", "All", "", False)
    page = index(state)

    expected_content = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("Network Inventory Database"),
        "\n",
        "System Administrator: ",
        bold("Bob"),
        "\nMaintenance Window: INACTIVE (Normal Operations)\n",
        "Total hosts currently monitored: 1",
    ]
    assert_equal(page, Page(state, expected_content))


def test_maintenance_page():
    state = State([], "Admin", "All", "", True)
    page = maintenance_page(state)

    expected_content = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("Maintenance Settings"),
        "\n",
        "Current Maintenance Status: ",
        bold("ENABLED"),
        "\n",
        Button("Toggle Maintenance Mode", toggle_maintenance),
        "\n",
        "--------------------------------------------------\n",
        bold("Administrator Settings\n"),
        "System Administrator: Admin\n",
        "Update Admin Operator Name: ",
        TextBox("new_admin", "Admin"),
        Button("Update Name", update_admin),
    ]
    assert_equal(page, Page(state, expected_content))


def test_update_admin():
    state = State([], "OldAdmin", "All", "", True)
    page = update_admin(state, "NewAdmin")

    assert_equal(state.admin_name, "NewAdmin")
    assert_equal(state.status_log, "Admin operator changed to: NewAdmin")
    assert_equal(page, maintenance_page(state))


def test_toggle_maintenance():
    state = State([], "Admin", "All", "", False)
    page = toggle_maintenance(state)

    assert_equal(state.maintenance_mode, True)
    assert_equal(state.status_log, "Maintenance Mode is now set to: True")
    assert_equal(page, maintenance_page(state))


def test_host_roster():
    host = Host("gw-01", "192.168.1.1", "Cisco IOS", 1, True, "Core switch")
    state = State([host], "Admin", "Cisco IOS", "", False)
    page = host_roster(state)

    expected_content = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("Network Host Roster"),
        "\n",
        "Filter by Operating System: ",
        SelectBox("os_filter", OS_FILTER_OPTIONS, "Cisco IOS"),
        Button("Apply OS Filter", apply_os_filter),
        "\n",
        "gw-01 (192.168.1.1) | OS: Cisco IOS",
        " | Ports: 1 | ",
        bold("[PATCH REQUIRED]"),
        "\n",
        italic("Notes: Core switch"),
        "\n",
        "--------------------------------------------------\n",
        bold("Toggle Patch Status for a Host:\n"),
        "Enter Exact Hostname: ",
        TextBox("target_hostname", ""),
        Button("Toggle Patch Status", toggle_patch_status),
        "\n",
    ]
    assert_equal(page, Page(state, expected_content))


def test_apply_os_filter():
    state = State([], "Admin", "All", "", False)
    page = apply_os_filter(state, "Linux")

    assert_equal(state.selected_os_filter, "Linux")
    assert_equal(state.status_log, "Host filter set to: Linux")
    assert_equal(page, host_roster(state))


def test_toggle_patch_status():
    host = Host("db-01", "10.0.0.5", "Linux", 1, False, "Main DB")
    state = State([host], "Admin", "All", "", False)
    page = toggle_patch_status(state, "db-01")

    assert_equal(host.needs_patching, True)
    assert_equal(state.status_log, "Toggled patch status for: db-01")
    assert_equal(page, host_roster(state))


def test_provision_host_page():
    state = State([], "Admin", "All", "", False)
    page = provision_host_page(state)

    expected_content = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("Provision New Network Asset"),
        "\n",
        "Hostname:\n",
        TextBox("hostname", "srv-new-01"),
        "\nIP Address:\n",
        TextBox("ip_address", "192.168.1.50"),
        "\nOperating System:\n",
        SelectBox("os_type", OS_OPTIONS, OS_OPTIONS[0]),
        "\nOpen Port Count (Estimated):\n",
        TextBox("port_count_str", "2"),
        "\nNeeds Patch: ",
        CheckBox("needs_patching", False),
        "\nRunning Services & Notes:\n",
        TextArea("notes", "SSH (22), Web Server (80)"),
        "\n",
        Button("Provision Host", save_new_host),
    ]
    assert_equal(page, Page(state, expected_content))


def test_save_new_host():
    state = State([], "Admin", "All", "", False)
    page = save_new_host(
        state,
        "backup-01",
        "192.168.1.99",
        "Linux",
        "3",
        False,
        "Storage node",
    )

    expected_host = Host("backup-01", "192.168.1.99", "Linux", 3, False, "Storage node")
    assert_equal(state.hosts, [expected_host])
    assert_equal(state.status_log, "Successfully provisioned host: backup-01")
    assert_equal(page, host_roster(state))


def test_vulnerability_audit():
    host1 = Host("app-01", "10.0.0.10", "Linux", 5, True, "Vulnerable service")
    host2 = Host("app-02", "10.0.0.11", "Linux", 2, False, "Safe node")
    state = State([host1, host2], "Admin", "All", "", False)
    page = vulnerability_audit(state)

    expected_content = [
        Button("Dashboard", index),
        Button("Host Roster", host_roster),
        Button("Provision New Host", provision_host_page),
        Button("Vulnerability Audit", vulnerability_audit),
        Button("Maintenance", maintenance_page),
        "\n",
        bold("Network Vulnerability Audit"),
        "\n",
        "- Monitored Assets: 2\n",
        "- Total Exposed Open Ports: 7\n",
        "- Unpatched Assets: 1\n",
        "- High-Risk Devices (Unpatched and >3 Open Ports): ",
        bold("1"),
        "\n",
    ]
    assert_equal(page, Page(state, expected_content))



test_make_navbar()
test_index()
test_maintenance_page()
test_update_admin()
test_toggle_maintenance()
test_host_roster()
test_apply_os_filter()
test_toggle_patch_status()
test_provision_host_page()
test_save_new_host()
test_vulnerability_audit()

start_server(initial_state)



