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
    
        # 1. Start an interactive shell
        remote_conn = client.invoke_shell()
        time.sleep(2)  # Wait for the login banner/prompt to clear
    
        # Clear the initial buffer (the banner/prompt)
        if remote_conn.recv_ready():
            remote_conn.recv(5000)

        commands = ["show version", "show disk"]
    
        with open(log_filename, "a") as log_file:
            log_file.write(f"\n{'='*50}\nSESSION START: {datetime.now()} | HOST: {hostname}\n{'='*50}\n")

            for cmd in commands:
                print(f"Executing: {cmd}")
                # 2. Send command with a newline
                remote_conn.send(cmd + "\n")
            
                # 3. Wait for the device to process and respond
                time.sleep(3) 
            
                # 4. Read the output from the buffer
                if remote_conn.recv_ready():
                    output = remote_conn.recv(10000).decode('utf-8', errors='ignore')
                    log_file.write(f"\nCOMMAND: {cmd}\nOUTPUT:\n{output}\n")
                else:
                    log_file.write(f"\nCOMMAND: {cmd}\nERROR: No output received\n")

        print(f"\nResults successfully logged to {log_filename}")
    except paramiko.AuthenticationException:
        print("Auth failed. Check username/password.")
    except Exception as e:
        print(f"Connection Error: {e}")
    finally:
        client.close()        
if __name__ == "__main__":
    run_infoblox_commands()
