####Fix to resolve Non Ouput iSSUES####
shell = client.invoke_shell()
time.sleep(1)
shell.recv(1000)  # Clear banner

for cmd in commands:
    print(f"Executing: {cmd}")
    shell.send(cmd + "\n")
    time.sleep(2)

    output = ""
    while shell.recv_ready():
        output += shell.recv(4096).decode('utf-8')

    writer.writerow({
        "Timestamp": timestamp,
        "Host": hostname,
        "Command": cmd,
        "Output": output.strip(),
        "Error": ""
    })
  ####Fix to resolve Non Ouput iSSUES####
