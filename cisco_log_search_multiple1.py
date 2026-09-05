#!/usr/bin/env python3
"""
Cisco log search multiple.py

Connects to multiple Cisco IOS routers over SSH (one after another, in a
loop) and searches each device's log for a user-supplied keyword using:

    show log | include <keyword>

Router IP addresses are not typed in manually. Instead, the user is
prompted for a CSV filename, and the script reads every IP address from
the 'ip_address' column of that file, connecting to each one in turn.

Expected CSV format (header row required):
    ip_address
    192.168.1.1
    192.168.1.2
    192.168.1.3

Note: This script does NOT use an enable password / enable mode. It
assumes the login user already has sufficient privileges to run show
commands (i.e. privilege level 15), so no "enable secret" is prompted
for or used.

This script does NOT modify any device configuration. It only reads
logs from each device.

The output of the "show log | include <keyword>" command for each
device is appended to a local log file, log_search_results.txt, in the
current working directory. The file is created automatically on first
run if it doesn't exist.

Requires:
    pip install netmiko

Usage:
    python3 cisco_log_search_multiple.py
"""

import sys
import csv
import time
import getpass
from datetime import datetime

# Name of the local results file that search output gets appended to.
# This lives in the current working directory, not a fixed absolute path.
RESULTS_FILE = "log_search_results.txt"

# Extra time (in seconds) to wait after issuing the search command on
# each device before moving on, to give slower devices/log searches
# time to fully return their output.
EXTRA_WAIT_SECONDS = 10

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
    Prompt the user for the CSV filename, shared login details, and the
    keyword to search for in each device's log. These are reused for
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

    # --- Keyword to search for in "show log | include <keyword>" ---
    keyword = input("Enter the keyword to search for in the device logs: ").strip()
    while not keyword:
        print("Keyword cannot be blank.")
        keyword = input("Enter the keyword to search for in the device logs: ").strip()

    # Return everything as a dict so main() can pass it around easily
    return {
        "ip_addresses": ip_addresses,
        "username": username,
        "password": password,
        "keyword": keyword,
    }


def log_to_file(label, content):
    """
    Append a labeled block of command output to the local results file.

    Opening in "a" (append) mode creates the file automatically if it
    doesn't already exist, and preserves prior runs' entries if it does.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RESULTS_FILE, "a") as f:
        f.write(f"\n=== {label} ({timestamp}) ===\n")
        f.write(content + "\n")


def process_device(ip_address, data, search_command):
    """
    Connect to a single router and search its log for the given
    keyword, printing and logging the result. Returns True on overall
    success, False on any failure, so the caller's loop can keep going
    to the next device.
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
        # the login account already having enough privilege to run show
        # commands, so no enable password is requested or used.

        # Run the log search command on this device.
        print(f"Searching logs for keyword: {data['keyword']}")
        search_output = conn.send_command(search_command)
        print(f"\n--- {search_command} ---")
        print(search_output)

        # Give the device/search a little extra time to fully settle
        # before moving on to the next one in the loop.
        time.sleep(EXTRA_WAIT_SECONDS)

        # Write this device's search output to the local results file.
        # The device IP is included in the label so entries from
        # different routers can be told apart in the shared results file.
        log_to_file(f"{ip_address} - {search_command}", search_output)

        print(f"\nSearch results for {ip_address} written to {RESULTS_FILE}")

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
    # and search keyword from the user, once, up front.
    data = get_inputs()

    # Build the IOS command used to search each device's log.
    search_command = f"show log | include {data['keyword']}"

    # Track results so we can print a final summary after the loop.
    successes = []
    failures = []

    # Loop over every IP address pulled from the CSV file, running the
    # log search against each device in turn.
    for ip_address in data["ip_addresses"]:
        result = process_device(ip_address, data, search_command)
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
