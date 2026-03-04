import paramiko
import getpass
import csv
import time
import os
from datetime import datetime


# -----------------------------------------------------------
# Function: Run commands on a single router
# Creates a unique CSV file for each router
# -----------------------------------------------------------
def run_commands_on_router(hostname, username, password):

    try:
        print(f"\n====================================")
        print(f"Connecting to {hostname}")
        print(f"====================================\n")

        # Create SSH client object
        ssh = paramiko.SSHClient()

        # Automatically accept unknown SSH keys (safe for lab use)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Establish SSH connection
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )

        # Open interactive shell session
        shell = ssh.invoke_shell()
        time.sleep(1)

        # Disable paging to prevent --More-- prompts
        shell.send("terminal length 0\n")
        time.sleep(1)
        shell.recv(65535)

        # List of commands to run
        commands = [
            "show version | include uptime",
            "show version | include returned",
            "show ip interface brief",
            "show ntp status | in Clock",
            "show ip route | inc 0.0.0.0"
        ]

        # Create a unique CSV filename per router
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{hostname}_changelog_{timestamp}.csv"

        # Open CSV file for this specific router
        with open(filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write CSV header row
            writer.writerow(["Timestamp", "Hostname", "Command", "Output"])

            # Loop through each command
            for command in commands:

                print(f"\nRunning command on {hostname}: {command}\n")

                # Send command to router
                shell.send(command + "\n")
                time.sleep(2)

                # Receive output
                output = shell.recv(65535).decode("utf-8")

                # Clean output (remove echoed command text)
                cleaned_output = output.replace(command, "").strip()

                # Print output to screen
                print(cleaned_output)

                # Write result to router-specific CSV
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    hostname,
                    command,
                    cleaned_output
                ])

        # Close SSH connection
        ssh.close()

        print(f"\nOutput saved to: {filename}\n")

    except Exception as e:
        print(f"\nError connecting to {hostname}: {e}\n")


# -----------------------------------------------------------
# Main Program
# -----------------------------------------------------------
def main():

    # Prompt for credentials once
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    # Open router list file
    with open("targethosts.csv", "r") as infile:
        reader = csv.DictReader(infile)

        # Loop through each router in CSV
        for row in reader:

            # Extract IP address from column
            hostname = row["IP_Address"].strip()

            # Run command function
            run_commands_on_router(hostname, username, password)

    print("\n===================================")
    print("Job completed successfully")
    print("===================================\n")


# Execute script
if __name__ == "__main__":
    main()
