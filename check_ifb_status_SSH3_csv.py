import paramiko
import getpass
from datetime import datetime
import time
import csv  # Built-in, no installation required!

def run_infoblox_commands():
    # User prompts for connection details
    hostname = input("Enter Infoblox hostname/IP: ")
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")
    
    # Filename with .csv extension
    csv_filename = "ifb_check_status_log_SSHV3.csv"
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\nConnecting to {hostname}...")
        client.connect(hostname, username=username, password=password, look_for_keys=False)
        
        commands = ["hostname -Abs", "hostname -I", "ifconfig", "netstat -nltu"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Open the CSV file for appending
        # newline='' prevents extra blank rows on some systems
        with open(csv_filename, mode='a', newline='') as csv_file:
            fieldnames = ["Timestamp", "Host", "Command", "Output", "Error"]
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

            # Write header only if the file is new/empty
            csv_file.seek(0, 2)
            if csv_file.tell() == 0:
                writer.writeheader()

            for cmd in commands:
                print(f"Executing: {cmd}")
                stdin, stdout, stderr = client.exec_command(cmd)
                
                output = stdout.read().decode('utf-8').strip()
                error = stderr.read().decode('utf-8').strip()
                
                # Write row directly to CSV
                writer.writerow({
                    "Timestamp": timestamp,
                    "Host": hostname,
                    "Command": cmd,
                    "Output": output,
                    "Error": error
                })
                time.sleep(1)

        print(f"\nResults successfully saved to {csv_filename}")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    run_infoblox_commands()
