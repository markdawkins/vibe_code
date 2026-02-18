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
        client.connect(hostname, username=username, password=password, look_for_keys=False, timeout=10)
        print("Connected successfully!")
        
        # Open an interactive shell session (sometimes needed for Infoblox)
        shell = client.invoke_shell()
        time.sleep(2)  # Wait for shell to initialize
        
        # Clear any initial banner/messages
        if shell.recv_ready():
            shell.recv(65535)
        
        # Infoblox commands (adjust these based on your actual commands)
        commands = [
            "show version",  # Changed from "show_ver" to "show version"
            "show disk",     # Changed from "show_disk" to "show disk"
            "show interface",
            "show network"
        ]
        
        # Open the log file in append mode ('a')
        with open(log_filename, "a") as log_file:
            # Write a timestamp header for the session
            log_file.write(f"\n{'='*50}\n")
            log_file.write(f"SESSION START: {datetime.now()} | HOST: {hostname}\n")
            log_file.write(f"{'='*50}\n")

            for cmd in commands:
                print(f"\nExecuting: {cmd}")
                
                # Send command
                shell.send(cmd + "\n")
                time.sleep(3)  # Wait for command to execute
                
                # Receive output
                output = ""
                while shell.recv_ready():
                    output += shell.recv(65535).decode('utf-8', errors='ignore')
                    time.sleep(1)
                
                # Alternative: using exec_command (uncomment if invoke_shell doesn't work)
                # stdin, stdout, stderr = client.exec_command(cmd)
                # output = stdout.read().decode('utf-8', errors='ignore').strip()
                # error = stderr.read().decode('utf-8', errors='ignore').strip()

                # Write to file
                log_file.write(f"\nCOMMAND: {cmd}\n")
                if output:
                    log_file.write(f"OUTPUT:\n{output}\n")
                    print(f"Output received ({len(output)} bytes)")
                else:
                    log_file.write("OUTPUT: (No output)\n")
                    print("No output received")
                
                time.sleep(2)
                
        print(f"\nResults successfully logged to {log_filename}")

    except paramiko.AuthenticationException:
        print("Authentication failed. Please check your credentials.")
    except paramiko.SSHException as e:
        print(f"SSH connection error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.close()
            print("Connection closed.")
        except:
            pass

if __name__ == "__main__":
    run_infoblox_commands()
