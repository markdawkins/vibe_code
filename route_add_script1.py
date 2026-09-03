#!/usr/bin/env python3
"""
cisco_add_route.py

Connects to a Cisco IOS router over SSH, adds a static route, verifies it,
saves the configuration, and displays confirmation output.

Requires:
    pip install netmiko

Usage:
    python3 cisco_add_route.py
"""

import sys
import getpass

try:
    from netmiko import ConnectHandler
    from netmiko.exceptions import (
        NetmikoTimeoutException,
        NetmikoAuthenticationException,
    )
except ImportError:
    print("This script requires the 'netmiko' library.")
    print("Install it with:  pip install netmiko")
    sys.exit(1)


def get_inputs():
    """Prompt the user for all required connection and configuration details."""
    ip_address = input("Enter the router IP address: ").strip()
    username = input("Enter the username: ").strip()
    password = getpass.getpass("Enter the login password: ")
    enable_password = getpass.getpass("Enter the enable password: ")
    network = input("Enter the new network to add (e.g. 10.10.10.0): ").strip()
    subnet_mask = input("Enter the subnet mask (e.g. 255.255.255.0): ").strip()
    next_hop = input("Enter the next-hop IP address for this network: ").strip()

    return {
        "ip_address": ip_address,
        "username": username,
        "password": password,
        "enable_password": enable_password,
        "network": network,
        "subnet_mask": subnet_mask,
        "next_hop": next_hop,
    }


def main():
    data = get_inputs()

    route_command = f"ip route {data['network']} {data['subnet_mask']} {data['next_hop']}"

    device = {
        "device_type": "cisco_ios",
        "host": data["ip_address"],
        "username": data["username"],
        "password": data["password"],
        "secret": data["enable_password"],
    }

    try:
        print(f"\nConnecting to {data['ip_address']}...")
        conn = ConnectHandler(**device)
        conn.enable()  # enter enable mode using the secret

        # 6. Add the new route to the running config
        print(f"Adding route: {route_command}")
        conn.send_config_set([route_command])

        # 7. Show the route table (all ip route lines) and display it
        show_output = conn.send_command("show run | include ip route")
        print("\n--- show run | include ip route ---")
        print(show_output)

        # 8. Check whether the new route was actually added
        if route_command in show_output:
            save_output = conn.send_command_timing("write mem")
            print("\n--- write mem output ---")
            print(save_output)
        else:
            print("error saving configuration")

        # 9. Task complete message
        print("\nTask Complete")

        # 10. Show the specific new network/subnet line and display it
        verify_command = f"show run | include {data['network']}"
        verify_output = conn.send_command(verify_command)
        print(f"\n--- {verify_command} ---")
        print(verify_output)

        conn.disconnect()

    except NetmikoAuthenticationException:
        print("Authentication failed. Check username/password/enable password.")
        sys.exit(1)
    except NetmikoTimeoutException:
        print(f"Connection to {data['ip_address']} timed out.")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
