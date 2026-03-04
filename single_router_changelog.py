import paramiko
import getpass
import csv
import time
from datetime import datetime


# -----------------------------------------------------------
# Main function
# -----------------------------------------------------------
def main():

    # Prompt user for router connection details
    hostname = input("Enter Cisco Router IP or Hostname: ")
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    try:
        print(f"\n====================================")
        print(f"Connecting to {hostname}")
        print(f"====================================\n")

        # Create SSH client object
        ssh = paramiko.SSHClient()

        # Automatically accept unknown SSH keys (lab-friendly)
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Establish SSH connection to router
        ssh.connect(
            hostname=hostname,
            username=username,
            password=password,
            timeout=10,
            look_for_keys=False,
            allow_agent=False
        )

        # Open an interactive shell session
        shell = ssh.invoke_shell()
        time.sleep(1)

        # Disable paging so output does not stop at "--More--"
        shell.send("terminal length 0\n")
        time.sleep(1)
        shell.recv(65535)  # Clear buffer

        # Commands to execute on router
        commands = [
            "show version | include uptime",
            "show version | include returned",
            "show ip interface brief",
            "show ntp status | in Clock",
            "show ip route | inc 0.0.0.0"
        ]

        # Create a single CSV file (timestamped to avoid overwrite)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{hostname}_changelog_{timestamp}.csv"

        # Open CSV file for writing
        with open(filename, "w", newline="") as csvfile:

            writer = csv.writer(csvfile)

            # Write header row
            writer.writerow(["Timestamp", "Hostname", "Command", "Output"])

            # Loop through each command
            for command in commands:

                print(f"\nRunning command: {command}\n")

                # Send command to router
                shell.send(command + "\n")
                time.sleep(2)

                # Receive output from router
                output = shell.recv(65535).decode("utf-8")

                # Remove echoed command text from output
                cleaned_output = output.replace(command, "").strip()

                # Print command output to screen
                print(cleaned_output)

                # Write command output to CSV file
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    hostname,
                    command,
                    cleaned_output
                ])

        # Close SSH connection
        ssh.close()

        print(f"\nOutput saved to: {filename}")

        print("\n===================================")
        print("Job completed successfully")
        print("===================================\n")

    except Exception as e:
        print(f"\nAn error occurred: {e}")


# Run the script
if __name__ == "__main__":
    main()
