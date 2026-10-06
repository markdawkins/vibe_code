#!/usr/bin/env python3
"""
Logs into a Nagios server over SSH, creates a new host config file in
/usr/local/nagios/etc/target_devices, then restarts Nagios.

Requires: pip install paramiko
"""

import sys
import paramiko

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
NAGIOS_HOST = "192.168.1.253"
SSH_USER = "mark"
SSH_PASS = "go"

TARGET_DIR = "/usr/local/nagios/etc/target_devices"
NAGIOS_BIN = "/usr/local/nagios/bin/nagios"
NAGIOS_CFG = "/usr/local/nagios/etc/nagios.cfg"

NEW_HOSTNAME = "new_server"
NEW_IP = "1.1.1.1"

# ---------------------------------------------------------------------------
# Config template (based on the ubmdsrvr1.cfg sample)
# __HOSTNAME__ and __IP__ are replaced at runtime.
# ---------------------------------------------------------------------------
CONFIG_TEMPLATE = """\
# __HOSTNAME__.CFG - SAMPLE OBJECT CONFIG FILE FOR MONITORING THIS MACHINE
#
#
# NOTE: This config file is intended to serve as an *extremely* simple
#       example of how you can create configuration entries to monitor
#       the local (Linux) machine.
#
###############################################################################



###############################################################################
#
# HOST DEFINITION
#
###############################################################################

# Define a host for the local machine

define host {

    use                     linux-server            ; Name of host template to use
                                                    ; This host definition will inherit all variables that are defined
                                                    ; in (or inherited by) the linux-server host template definition.
    host_name               __HOSTNAME__
    alias                   __HOSTNAME__
    address                 __IP__
    _SNMP_COMMUNITY         cville
    max_check_attempts      5
    check_period            24x7
    notification_interval   30
    notification_period     24x7
    contact_groups          admins
}

############

###############################################################################
#
# HOST GROUP DEFINITION
#
###############################################################################

# Define an optional hostgroup for Linux machines

#define hostgroup {

#    hostgroup_name          proxmox_servers           ; The name of the hostgroup
#    alias                   proxmox_servers           ; Long name of the group
#    members                 __HOSTNAME__               ; Comma separated list of hosts that belong to this group
#}



###############################################################################
#
# SERVICE DEFINITIONS
#
###############################################################################

# Define a service to "ping" the local machine

define service {

    use                     local-service           ; Name of service template to use
    host_name               __HOSTNAME__
    service_description     PING
    check_command           check_ping!100.0,20%!500.0,60%
}




# Define a service to check the number of currently logged in
# users on the local machine.  Warning if > 20 users, critical
# if > 50 users.

#define service {
#
#    use                     local-service           ; Name of service template to use
#    host_name               __HOSTNAME__
#    service_description     Current Users
#    check_command           check_local_users!20!50
#}



# Define a service to check the number of currently running procs
# on the local machine.  Warning if > 250 processes, critical if
# > 400 processes.

#define service {

#    use                     local-service           ; Name of service template to use
#    host_name               __HOSTNAME__
#    service_description     Total Processes
#    check_command           check_local_procs!250!400!RSZDT
#}



# Define a service to check the load on the local machine.
#
#define service {

#    use                     local-service           ; Name of service template to use
#    host_name               __HOSTNAME__
#    service_description     Current Load
#    check_command           check_local_load!5.0,4.0,3.0!10.0,6.0,4.0
#}



# Define a service to check the swap usage the local machine.
# Critical if less than 10% of swap is free, warning if less than 20% is free

#define service {

#    use                     local-service           ; Name of service template to use
#    host_name               __HOSTNAME__
#    service_description     Swap Usage
#    check_command           check_local_swap!20%!10%
#}



# Define a service to check SSH on the local machine.
# Disable notifications for this service by default, as not all users may have SSH enabled.

define service {

    use                     local-service           ; Name of service template to use
    host_name               __HOSTNAME__
    service_description     SSH
    check_command           check_ssh
    notifications_enabled   0
}



# Define a service to check HTTP on the local machine.
# Disable notifications for this service by default, as not all users may have HTTP enabled.

define service {

    use                     local-service           ; Name of service template to use
    host_name               __HOSTNAME__
    service_description     Emby Server
    check_command           check_tcp_8096
    notifications_enabled   0
}


#######Define service to check disk Utilization

#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Disk Utilization sda1
#    check_command           check_nrpe!check_sda1
#}


##########Server Services - Disk sdc

#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Disk Utilization Media Folder
#    check_command           check_nrpe!check_sdc
#}

##########################Check processes ##############

#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Check Processes
#    check_command           check_nrpe!check_total_procs
#}

#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Check Zombie Processes
#    check_command           check_nrpe!check_zombie_procs
#}
##############################################Check Load#########
#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Check Load
#    check_command           check_nrpe!check_load
#}

#define service{
#    use                     generic-service
#    host_name               __HOSTNAME__
#    service_description     Check Users
#    check_command           check_nrpe!check_users
#}
"""


def run(ssh, command):
    """Run a command over SSH; return (exit_status, stdout, stderr)."""
    print(f"$ {command}")
    _, stdout, stderr = ssh.exec_command(command)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    status = stdout.channel.recv_exit_status()
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return status, out, err


def main():
    config_text = (
        CONFIG_TEMPLATE
        .replace("__HOSTNAME__", NEW_HOSTNAME)
        .replace("__IP__", NEW_IP)
    )
    remote_path = f"{TARGET_DIR}/{NEW_HOSTNAME}.cfg"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        print(f"Connecting to {NAGIOS_HOST} as {SSH_USER}...")
        ssh.connect(NAGIOS_HOST, username=SSH_USER, password=SSH_PASS, timeout=15)

        # Change to the target directory (each exec_command is its own shell,
        # so we verify the directory exists and then write the file by full path).
        status, _, _ = run(ssh, f"cd {TARGET_DIR} && pwd")
        if status != 0:
            sys.exit(f"Directory {TARGET_DIR} not found on the Nagios server.")

        # Refuse to overwrite an existing config
        status, _, _ = run(ssh, f"test -e {remote_path}")
        if status == 0:
            sys.exit(f"{remote_path} already exists; aborting so it isn't overwritten.")

        # Write the config file via SFTP
        print(f"Creating {remote_path}...")
        sftp = ssh.open_sftp()
        with sftp.open(remote_path, "w") as f:
            f.write(config_text)
        sftp.close()

        # Match ownership of the other files in the directory (non-fatal if it fails)
        run(ssh, f"chown nagios:nagios {remote_path}")

        # Validate the Nagios configuration before restarting
        status, _, _ = run(ssh, f"{NAGIOS_BIN} -v {NAGIOS_CFG}")
        if status != 0:
            sys.exit("Nagios config verification failed; NOT restarting Nagios.")

        # Restart Nagios
        status, _, _ = run(ssh, "sudo systemctl restart nagios")
        if status != 0:
            sys.exit("Failed to restart Nagios.")

        # Confirm it came back up
        run(ssh, "systemctl is-active nagios")
        print(f"Done. Host '{NEW_HOSTNAME}' ({NEW_IP}) added to Nagios.")

    except paramiko.AuthenticationException:
        sys.exit("SSH authentication failed. Check the username/password.")
    except Exception as exc:
        sys.exit(f"Error: {exc}")
    finally:
        ssh.close()


if __name__ == "__main__":
