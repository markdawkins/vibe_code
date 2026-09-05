#!/usr/bin/env python3
"""
Cisco delete route multiple.py

Connects to multiple Cisco IOS routers over SSH (one after another, in a
loop) and REMOVES the same static route from each, verifies the removal,
saves the configuration, and displays confirmation output.

Router IP addresses are not typed in manually. Instead, the user is
prompted for a CSV filename, and the script reads every IP address from
the 'ip_address' column of that file, connecting to each one in turn.

Expected CSV format (header row required):
    ip_address
    192.168.1.1
    192.168.1.2
    192.168.1.3

Note: This script does NOT use an enable password / enable mode. It
assumes the login user already has sufficient privileges to make
configuration changes (i.e. privilege level 15), so no "enable secret"
is prompted for or used.

The output of both verify_commands (the network-specific "show run"
check and the "show log | include CONFIG" check) is appended to a local
log file, cisco_delete_route_log.txt, in the current working directory.
The file is created automatically on first run if it doesn't exist.

Requires:
    pip install netmiko

Usage:
    python3 "Cisco delete route multiple.py"
"""

import sys
import csv
import getpass
from datetime import datetime

# Name of the local log file that verify_command output gets appended to.
# This lives in the current working directory, not a fixed absolute path.
LOG_FILE = "cisco_delete_route_log.txt"

# Netmiko handles the SSH session and Cisco-specific command syntax
# (config mode, paging, prompt detection, etc.)
try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import (
        NetmikoTimeoutException,
        NetmikoAuthenticationException,
    )
except ImportError:
    # Fail early with a clear message rather than a confusing traceback
    # if the required library isn't installed.
    print("This script requires the 'netmiko' library.")
    print("Install it with:  pip install netmiko")
    sys.exit(1)


def load_ip_addresses(filename):
    """
    Read a CSV file and return a list of IP addresses from its
    'ip_address' column.

    Using csv.DictReader lets us pull values out by column name (rather
    than a fixed column position), so the 'ip_address' column can be in
    any position in the file as long as the header row is present.
    """
    ip_list = []
    try:
        with open(filename, newline="") as csvfile:
            reader = csv.DictReader(csvfile)

            # Make sure the expected column actually exists before looping,
            # so we can give a clear error instead of a KeyError per row.
            if reader.fieldnames is None or "ip_address" not in reader.fieldnames:
                print("Error: CSV file must contain an 'ip_address' column header.")
                sys.exit(1)

            for row in reader:
                ip = row["ip_address"].strip()
                if ip:  # skip any blank rows
                    ip_list.append(ip)

    except FileNotFoundError:
        print(f"Error: file '{filename}' was not found.")
        sys.exit(1)

    if not ip_list:
        print("Error: no IP addresses were found in the 'ip_address' column.")
        sys.exit(1)

    return ip_list


def get_inputs():
    """
    Prompt the user for the CSV filename plus all shared login and
    route details. These credentials and route settings are reused for
    every device read from the CSV.
    """
    # --- CSV file containing the list of router IP addresses ---
    csv_filename = input("Enter the CSV filename containing IP addresses: ").strip()
    ip_addresses = load_ip_addresses(csv_filename)

    # --- Login details (shared across all devices in the loop) ---
    username = input("Enter the username: ").strip()

    # getpass hides the typed characters so the password isn't shown on
    # screen or captured in shell/terminal history/scrollback.
    password = getpass.getpass("Enter the login password: ")

    # --- Static route to remove (also shared across all devices) ---
    network = input("Enter the network to delete (e.g. 10.10.10.0): ").strip()
    subnet_mask = input("Enter the subnet mask (e.g. 255.255.255.0): ").strip()
    next_hop = input("Enter the next-hop IP address for this network: ").strip()

    # Return everything as a dict so main() can pass it around easily
    return {
        "ip_addresses": ip_addresses,
        "username": username,
        "password": password,
        "network": network,
        "subnet_mask": subnet_mask,
        "next_hop": next_hop,
    }


def log_to_file(label, content):
    """
    Append a labeled block of command output to the local log file.

    Opening in "a" (append) mode creates the file automatically if it
    doesn't already exist, and preserves prior runs' entries if it does.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"\n=== {label} ({timestamp}) ===\n")
        f.write(content + "\n")


def process_device(ip_address, data, route_command, original_route):
    """
    Connect to a single router and run the full delete-route workflow:
    remove the route, verify it's gone, save the config if successful,
    and log the verification output. Returns True on overall success,
    False on any failure, so the caller's loop can keep going to the
    next device.
    """
    # Netmiko connection parameters for this specific device.
    # No "secret" key is set here since enable mode is not used.
    device = {
        "device_type": "cisco_ios",
        "host": ip_address,
        "username": data["username"],
        "password": data["password"],
    }

    try:
        # Open the SSH session to the router
        print(f"\nConnecting to {ip_address}...")
        conn = ConnectHandler(**device)

        # No conn.enable() call here on purpose - this script relies on
        # the login account already having enough privilege to configure
        # the device, so no enable password is requested or used.

        # Remove the static route from the running config.
        # send_config_set() automatically enters/exits "configure terminal".
        print(f"Removing route: {route_command}")
        conn.send_config_set([route_command])

        # Display all static routes currently in the running config so the
        # user can visually confirm the route is gone.
        show_output = conn.send_command("show run | include ip route")
        print("\n--- show run | include ip route ---")
        print(show_output)

        # If the original route line is no longer present, the deletion
        # succeeded, so save the config. Otherwise, warn the user instead
        # of saving - the route may still be active.
        if original_route not in show_output:
            # send_command_timing is used instead of send_command because
            # "write mem" can prompt for confirmation on some IOS versions
            # and doesn't always return to a predictable prompt pattern.
            save_output = conn.send_command_timing("write mem")
            print("\n--- write mem output ---")
            print(save_output)
        else:
            print("error saving configuration")

        # Simple confirmation that this device's workflow has finished
        print(f"\nTask Complete for {ip_address}")

        # Show just the running-config line(s) matching the deleted
        # network, so the user can visually confirm it's no longer there.
        verify_command = f"show run | include {data['network']}"
        verify_output = conn.send_command(verify_command)
        print(f"\n--- {verify_command} ---")
        print(verify_output)

        # Write this verify_command's output to the local log file.
        # The device IP is included in the label so entries from
        # different routers can be told apart in the shared log file.
        log_to_file(f"{ip_address} - {verify_command}", verify_output)

        # Additional verification: check the router's log for any CONFIG
        # entries (e.g. "%SYS-5-CONFIG_I: Configured from console...").
        # This helps confirm a configuration change was actually logged.
        log_verify_command = "show log | include CONFIG"
        log_verify_output = conn.send_command(log_verify_command)
        print(f"\n--- {log_verify_command} ---")
        print(log_verify_output)

        # Write this verify_command's output to the local log file too
        log_to_file(f"{ip_address} - {log_verify_command}", log_verify_output)

        print(f"\nVerify command output for {ip_address} written to {LOG_FILE}")

        # Cleanly close the SSH session
        conn.disconnect()
        return True

    # Handle common, predictable failure cases with clear messages instead
    # of raw stack traces. These are caught per-device (rather than
    # exiting the whole script) so the loop can move on to the next IP.
    except NetmikoAuthenticationException:
        print(f"Authentication failed for {ip_address}. Check username/password.")
        return False
    except NetmikoTimeoutException:
        print(f"Connection to {ip_address} timed out.")
        return False
    except Exception as e:
        # Catch-all for anything unexpected (unreachable host, bad command
        # syntax rejected by the device, etc.)
        print(f"An unexpected error occurred with {ip_address}: {e}")
        return False


def main():
    # Gather the CSV filename (and derived IP list), login credentials,
    # and route info from the user, once, up front.
    data = get_inputs()

    # Build the IOS command to remove the static route. Prefixing an
    # existing config line with "no" removes it, e.g.:
    #   no ip route 10.10.10.0 255.255.255.0 192.168.1.1
    route_command = f"no ip route {data['network']} {data['subnet_mask']} {data['next_hop']}"

    # Build the original (non-"no") route line so we can check whether
    # it still exists in each device's config after the delete attempt.
    original_route = f"ip route {data['network']} {data['subnet_mask']} {data['next_hop']}"

    # Track results so we can print a final summary after the loop.
    successes = []
    failures = []

    # Loop over every IP address pulled from the CSV file, running the
    # full delete-route workflow against each device in turn.
    for ip_address in data["ip_addresses"]:
        result = process_device(ip_address, data, route_command, original_route)
        if result:
            successes.append(ip_address)
        else:
            failures.append(ip_address)

    # Final summary across all devices processed in this run.
    print("\n=== Summary ===")
    print(f"Succeeded: {len(successes)} -> {successes}")
    print(f"Failed:    {len(failures)} -> {failures}")

    # Exit with a non-zero status if any device failed, so this script
    # plays nicely if it's ever called from another automation tool.
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
