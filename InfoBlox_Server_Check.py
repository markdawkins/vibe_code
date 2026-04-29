#### This script checks multiple hosts simultaneously and adds multithreading up to 10 sessions #####
##Make sure to updated the commands below with the commands you need to use to collect data #####
### Also a seed file is required for the IP addresses. I used a file called targethosts.csv and it is called out here but you can change of course. ####
#### The output file ifb_check_status_log_SSHV5.csv file  can be renamed but it should be in ths folder unless you are pointing to some other well known file##
import paramiko
import getpass
import csv
import time
import socket
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# =========================
# CONFIGURATION
# =========================
MAX_THREADS = 10          # Number of concurrent SSH sessions
RETRY_COUNT = 3           # Retry attempts per host
RETRY_DELAY = 10          # Seconds between retries
SSH_TIMEOUT = 10          # SSH connection timeout
COMMAND_DELAY = 1         # Delay between commands

TARGET_FILE = "targethosts.csv"
OUTPUT_FILE = "ifb_check_status_log_SSHV5.csv"

COMMANDS = [
    "hostname -Abs",
    "hostname -I",
    "lsblk -a"
]

# Thread lock for safe CSV writing
csv_lock = threading.Lock()


# =========================
# SSH EXECUTION FUNCTION
# =========================
def ssh_to_host(hostname, username, password):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for attempt in range(1, RETRY_COUNT + 1):

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            print(f"[{hostname}] Attempt {attempt} connecting...")

            client.connect(
                hostname=hostname,
                username=username,
                password=password,
                look_for_keys=False,
                timeout=SSH_TIMEOUT,
                banner_timeout=SSH_TIMEOUT,
                auth_timeout=SSH_TIMEOUT
            )

            print(f"[{hostname}] Connected successfully")

            results = []

            for cmd in COMMANDS:

                stdin, stdout, stderr = client.exec_command(cmd)

                output = stdout.read().decode().strip()
                error = stderr.read().decode().strip()

                results.append({
                    "Timestamp": timestamp,
                    "Host": hostname,
                    "Command": cmd,
                    "Output": output,
                    "Error": error
                })

                time.sleep(COMMAND_DELAY)

            client.close()

            return results

        except paramiko.AuthenticationException:
            print(f"[{hostname}] Authentication failed")
            return [{
                "Timestamp": timestamp,
                "Host": hostname,
                "Command": "AUTH",
                "Output": "",
                "Error": "Authentication failed"
            }]

        except (socket.timeout, paramiko.SSHException, Exception) as e:

            print(f"[{hostname}] Attempt {attempt} failed: {e}")

            if attempt < RETRY_COUNT:
                print(f"[{hostname}] Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                return [{
                    "Timestamp": timestamp,
                    "Host": hostname,
                    "Command": "CONNECT",
                    "Output": "",
                    "Error": str(e)
                }]

        finally:
            client.close()


# =========================
# CSV WRITE FUNCTION
# =========================
def write_results(results):

    with csv_lock:

        with open(OUTPUT_FILE, "a", newline="") as file:

            fieldnames = ["Timestamp", "Host", "Command", "Output", "Error"]
            writer = csv.DictWriter(file, fieldnames=fieldnames)

            file.seek(0, 2)
            if file.tell() == 0:
                writer.writeheader()

            for row in results:
                writer.writerow(row)


# =========================
# LOAD HOSTS
# =========================
def load_hosts():

    hosts = []

    with open(TARGET_FILE, newline="") as csvfile:

        reader = csv.DictReader(csvfile)

        for row in reader:
            hosts.append(row["IP_Address"].strip())

    return hosts


# =========================
# MAIN EXECUTION
# =========================
def run_infoblox_commands():

    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    hosts = load_hosts()

    print(f"\nLoaded {len(hosts)} hosts")
    print(f"Running with {MAX_THREADS} concurrent threads\n")

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:

        future_to_host = {
            executor.submit(ssh_to_host, host, username, password): host
            for host in hosts
        }

        for future in as_completed(future_to_host):

            host = future_to_host[future]

            try:
                results = future.result()
                write_results(results)
                print(f"[{host}] Results saved")

            except Exception as e:
                print(f"[{host}] Unexpected error: {e}")

    print("\nAll hosts processed.")


# =========================
# ENTRY POINT
# =========================
if __name__ == "__main__":
    run_infoblox_commands()
