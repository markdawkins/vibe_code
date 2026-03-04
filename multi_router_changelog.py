import paramiko
import getpass
import csv
import time
from datetime import datetime

# --------------------------------------------
# Function: Run commands on a single router
# --------------------------------------------
def run_commands_on_router(hostname, username, password, writer):
    try:
        print(f"\n===============================")
        print(f"Connecting to {hostname}")
        print(f"===============================\n")

        # Create SSH client object
        ssh = paramiko.SSHClient()

        # Automatically add unknown host keys (lab-safe)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to the router
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

        # Disable paging so output is not interrupted
        shell.send("terminal length 0\n")
        time.sleep(1)
        shell.recv(65535)

        # List of commands to execute
        commands = [
            "show version | include uptime",
            "show version | include returned",
            "show ip interface brief",
            "show ntp status | in Clock",
            "show ip route | inc 0.0.0.0"
        ]

        # Loop through each command
        for command in commands:
            print(f"\nRunning command on {hostname}: {command}\n")

            # Send command
            shell.send(command + "\n")
            time.sleep(2)

            # Receive output
            output = shell.recv(65535).decode("utf-8")

            # Clean output by removing echoed command
            cleaned_output = output.replace(command, "").strip()

            # Print output to screen
            print(cleaned_output)

            # Write output to CSV
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                hostname,
                command,
                cleaned_output
            ])

        # Close SSH connection
        ssh.close()

    except Exception as e:
        print(f"\nError connecting to {hostname}: {e}\n")

        # Log error to CSV
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hostname,
            "CONNECTION FAILED",
            str(e)
        ])


# --------------------------------------------
# Main Program
# --------------------------------------------
def main():

    # Prompt user once for credentials
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    # Open output CSV file for writing results
    with open("changelog.csv", "a", newline="") as outfile:

        writer = csv.writer(outfile)

        # Write CSV header row
        writer.writerow(["Timestamp", "Hostname", "Command", "Output"])

        # Open the router list CSV file
        with open("targethosts.csv", "r") as infile:

            reader = csv.DictReader(infile)

            # Loop through each row in targethosts.csv
            for row in reader:

                # Extract IP address from column named IP_Address
                hostname = row["IP_Address"].strip()

                # Run commands on this router
                run_commands_on_router(hostname, username, password, writer)

    print("\n===================================")
    print("Job completed successfully")
    print("===================================\n")


# Run script
if __name__ == "__main__":
    main()
