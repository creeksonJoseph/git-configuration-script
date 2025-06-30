import os
import subprocess

# Step 1: Get user info
name = input("👤 Git username: ")
email = input("📧 Git email: ")
key_name = input("🔐 SSH key name (no spaces): ")

# Set project path (your target folder)
project_path = "/home/creeksonjoseph/others/bree"
ssh_path = f"~/.ssh/{key_name}"
ssh_path_expanded = os.path.expanduser(ssh_path)

# Step 2: Generate SSH key
print("🔐 Generating SSH key...")
subprocess.run([
    "ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email,
    "-f", ssh_path_expanded,
    "-N", ""  # No passphrase
])

# Step 3: Initialize Git repo if not already done
os.chdir(project_path)
if not os.path.isdir(".git"):
    subprocess.run(["git", "init"])

# Step 4: Set local Git config
print("🛠️ Setting local Git config...")
subprocess.run(["git", "config", "user.name", name])
subprocess.run(["git", "config", "user.email", email])
subprocess.run(["git", "config", "core.sshCommand", f"ssh -i {ssh_path_expanded} -F /dev/null"])

# Step 5: Start SSH agent & add the key
print("🚀 Adding key to SSH agent...")
subprocess.run("eval $(ssh-agent -s)", shell=True)
subprocess.run(["ssh-add", ssh_path_expanded])

# Step 6: Show public key
print("📋 Public SSH Key:")
with open(f"{ssh_path_expanded}.pub", "r") as pubkey_file:
    print(pubkey_file.read())

print("\n✅ All done. Paste that key in your GitHub SSH settings.")

