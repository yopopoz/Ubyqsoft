import paramiko
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

hostname = "82.112.253.118"
port = 22
username = "root"
password = "Ubyq2026@Afida"

try:
    print(f"Connecting to {hostname}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, port, username, password)
    
    commands = [
        "cd /opt/UBYQ && git pull origin main",
        "cd /opt/UBYQ && docker compose -f docker-compose.prod.yml build --no-cache backend",
        "cd /opt/UBYQ && docker compose -f docker-compose.prod.yml up -d backend"
    ]
    
    for command in commands:
        print(f"Executing: {command}")
        stdin, stdout, stderr = client.exec_command(command)
        
        # Print output in real-time if necessary, or just wait
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        if out:
            print("STDOUT:")
            print(out)
        if err:
            print("STDERR:")
            print(err)
            
        print(f"Exit status: {exit_status}\n")
        
    client.close()
    print("Deployment script finished successfully.")
    
except Exception as e:
    print(f"Error during SSH connection: {e}")
