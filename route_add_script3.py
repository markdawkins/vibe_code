#!/usr/bin/env python3
"""
route_add_script3.py

Connects to a Cisco IOS router over SSH, adds a static route, verifies it,
saves the configuration, and displays confirmation output.

The output of both verify_commands (the network-specific "show run"
check and the "show log | include CONFIG" check) is appended to a local
log file, cisco_add_route_log.txt, in the current working directory.
The file is created automatically on first run if it doesn't exist.

Requires:
    pip install netmiko

Usage:
    python3 cisco_add_route.py
"""

import sys
import getpass
from datetime import datetime

# Name of the local log file that verify_command output gets appended to.
# This lives in the current working directory, not a fixed absolute path.
LOG_FILE = "cisco_add_route_log.txt"

# Netmiko handles the SSH session and Cisco-specific command syntax
# (config mode, enable mode, paging, prompt detection, etc.)
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


def get_inputs():
    """Prompt the user for all required connection and configuration details."""
    # --- Device connection details ---
    ip_address = input("Enter the router IP address: ").strip()
    username = input("Enter the username: ").strip()

    # getpass hides the typed characters so passwords aren't shown on screen
    # or captured in shell/terminal history/scrollback.
    password = getpass.getpass("Enter the login password: ")
    enable_password = getpass.getpass("Enter the enable password: ")

    # --- New static route details ---
    network = input("Enter the new network to add (e.g. 10.10.10.0): ").strip()
    subnet_mask = input("Enter the subnet mask (e.g. 255.255.255.0): ").strip()
    next_hop = input("Enter the next-hop IP address for this network: ").strip()

    # Return everything as a dict so main() can pass it around easily
    return {
        "ip_address": ip_address,
        "username": username,
        "password": password,
        "enable_password": enable_password,
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


def main():
    # Step 1-5: gather all connection and route info from the user
    data = get_inputs()

    # Build the IOS static route command, e.g.:
    #   ip route 10.10.10.0 255.255.255.0 192.168.1.1
    route_command = f"ip route {data['network']} {data['subnet_mask']} {data['next_hop']}"

    # Netmiko connection parameters for a Cisco IOS device
    device = {
        "device_type": "cisco_ios",
        "host": data["ip_address"],
        "username": data["username"],
        "password": data["password"],
        "secret": data["enable_password"],  # used by conn.enable() below
    }

    try:
        # Open the SSH session to the router
        print(f"\nConnecting to {data['ip_address']}...")
        conn = ConnectHandler(**device)

        # Elevate to privileged EXEC (enable) mode using the enable secret
        conn.enable()

        # Step 6: Add the new route to the running config.
        # send_config_set() automatically enters/exits "configure terminal".
        print(f"Adding route: {route_command}")
        conn.send_config_set([route_command])

        # Step 7: Display all static routes currently in the running config
        show_output = conn.send_command("show run | include ip route")
        print("\n--- show run | include ip route ---")
        print(show_output)

        # Step 8: Confirm the exact route line is present before saving.
        # If it's missing, something went wrong applying the config, so we
        # skip "write mem" and warn the user instead of saving a bad state.
        if route_command in show_output:
            # send_command_timing is used instead of send_command because
            # "write mem" can prompt for confirmation on some IOS versions
            # and doesn't always return to a predictable prompt pattern.
            save_output = conn.send_command_timing("write mem")
            print("\n--- write mem output ---")
            print(save_output)
        else:
            print("error saving configuration")

        # Step 9: Simple confirmation that the workflow has finished
        print("\nTask Complete")

        # Step 10: Show just the running-config line(s) matching the new
        # network, so the user can visually confirm the specific route.
        verify_command = f"show run | include {data['network']}"
        verify_output = conn.send_command(verify_command)
        print(f"\n--- {verify_command} ---")
        print(verify_output)

        # Write this verify_command's output to the local log file
        log_to_file(verify_command, verify_output)

        # Additional verification: check the router's log for any CONFIG
        # entries (e.g. "%SYS-5-CONFIG_I: Configured from console...").
        # This helps confirm a configuration change was actually logged.
        log_verify_command = "show log | include CONFIG"
        log_verify_output = conn.send_command(log_verify_command)
        print(f"\n--- {log_verify_command} ---")
        print(log_verify_output)

        # Write this verify_command's output to the local log file too
        log_to_file(log_verify_command, log_verify_output)

        print(f"\nVerify command output written to {LOG_FILE}")

        # Cleanly close the SSH session
        conn.disconnect()

    # Handle common, predictable failure cases with clear messages instead
    # of raw stack traces.
    except NetmikoAuthenticationException:
        print("Authentication failed. Check username/password/enable password.")
        sys.exit(1)
    except NetmikoTimeoutException:
        print(f"Connection to {data['ip_address']} timed out.")
        sys.exit(1)
    except Exception as e:
        # Catch-all for anything unexpected (unreachable host, bad command
        # syntax rejected by the device, etc.)
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
