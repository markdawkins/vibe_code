#!/usr/bin/env python3

import paramiko
import getpass

def main():
    # Get credentials
    ip = input("Enter F5 device IP: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    try:
        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=10)
        
        print("\n" + "="*60)
        print("SSH CONNECTIONS ON PORT 22")
        print("="*60)
        
        # CORRECT: Direct bash command - no 'tmsh' prefix needed
        stdin, stdout, stderr = ssh.exec_command('bash -c "netstat -an | grep :22"')
        
        # Print output line by line
        for line in stdout:
            print(line.rstrip())
        
        ssh.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()