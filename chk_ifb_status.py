import paramiko
import getpass
from datetime import datetime
import time

def run_infoblox_commands():
    # User prompts for connection details
    hostname = input("Enter Infoblox Hostname/IP: ")
    username = input("Enter Username: ")
    password = getpass.getpass("Enter Password: ")

    log_filename = "ifb_check_status_log.txt"
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"\nConnecting to {hostname}...")
        client.connect(hostname, username=username, password=password, look_for_keys=False)
        
        commands = ["show version", "show disk"]
        
        # Open the log file in append mode ('a')
        with open(log_filename, "a") as log_file:
            # Write a timestamp header for the session
            log_file.write(f"\n{'='*50}\n")
            log_file.write(f"SESSION START: {datetime.now()} | HOST: {hostname}\n")
            log_file.write(f"{'='*50}\n")

            for cmd in commands:
                print(f"Executing: {cmd}")
                stdin, stdout, stderr = client.exec_command(cmd)
                
                output = stdout.read().decode('utf-8').strip()
                error = stderr.read().decode('utf-8').strip()

                # Write to file
                log_file.write(f"\nCOMMAND: {cmd}\n")
                if output:
                    log_file.write(f"OUTPUT:\n{output}\n")
                if error:
                    log_file.write(f"ERROR:\n{error}\n")
                time.sleep(5)
        print(f"\nResults successfully logged to {log_filename}")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()
        print("Connection closed.")

if __name__ == "__main__":
    run_infoblox_commands()
