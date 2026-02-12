#!/usr/bin/env python3
import paramiko
import getpass
import time

def main():
    # Get credentials
    ip = input("Enter F5 device IP: ")
    tcp_port = input("Enter tcp port: ")
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    
    try:
        # SSH connection
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, username=username, password=password, timeout=10)
        
        print("\n" + "="*60)
        print("TCP CONNECTIONS ON PORT", tcp_port)
        print("="*60)
        
        # CORRECT: Direct bash command - no 'tmsh' prefix needed
        stdin, stdout, stderr = ssh.exec_command('bash -c "netstat -an | grep :' + str(tcp_port) +'"')
        
        
        # Print output line by line
        for line in stdout:
            print(line.rstrip())
        
        
        print("\n" + "="*60)
        print("END OF SCRIPT.SCRIPT WILL CLOSE IN 30 SECONDS ")
        print("="*60)
        time.sleep(30)
        ssh.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
