import paramiko
import getpass
import csv
import time
from datetime import datetime

def run_commands():
    # Prompt for connection details
    hostname = input("Enter Cisco Router IP or Hostname: ")
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    # Commands to execute
    commands = [
        "show version | include uptime",
        "show version | include returned",
        "show ip interface brief",
        "show ntp status | in Clock",
        "show ip route | inc 0.0.0.0"
    ]

    try:
        print(f"\nConnecting to {hostname}...\n")

        # Create SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Connect to router
        ssh.connect(hostname=hostname, username=username, password=password, timeout=10)

        # Open interactive shell
        shell = ssh.invoke_shell()
        time.sleep(1)

        # Disable paging
        shell.send("terminal length 0\n")
        time.sleep(1)
        shell.recv(65535)

        # Open CSV file
        with open("changelog.csv", "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Timestamp", "Hostname", "Command", "Output"])

            for command in commands:
                print(f"\nRunning command: {command}\n")

                shell.send(command + "\n")
                time.sleep(2)

                output = shell.recv(65535).decode("utf-8")

                # Clean output
                cleaned_output = output.replace(command, "").strip()

                # Print to screen
                print(cleaned_output)

                # Write to CSV
                writer.writerow([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    hostname,
                    command,
                    cleaned_output
                ])

        ssh.close()

        print("\n===================================")
        print("Job completed successfully")
        print("===================================\n")

    except Exception as e:
        print(f"\nAn error occurred: {e}")


if __name__ == "__main__":
    run_commands()
