#!/usr/bin/env python3

import paramiko
import getpass
import time
from datetime import datetime

INTERVAL_SECONDS = 300      # 5 minutes
TOTAL_RUNTIME_SECONDS = 3600  # 1 hour

def main():
    # Get credentials once
    ip = input("Enter F5 device IP: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")

    start_time = time.time()
    run_count = 0

    while time.time() - start_time < TOTAL_RUNTIME_SECONDS:
        run_count += 1
        print("\n" + "=" * 60)
        print(f"RUN #{run_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("SSH CONNECTIONS ON PORT 22")
        print("=" * 60)

        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=10)

            stdin, stdout, stderr = ssh.exec_command(
                'bash -c "netstat -an | grep :22"'
            )

            for line in stdout:
                print(line.rstrip())

            ssh.close()

        except Exception as e:
            print(f"Error: {e}")

        # Sleep unless this was the final run
        if time.time() - start_time < TOTAL_RUNTIME_SECONDS:
            time.sleep(INTERVAL_SECONDS)

    print("\nCompleted 1 hour of monitoring.")

if __name__ == "__main__":
    main()