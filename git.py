import os
import platform
import subprocess

# Step 1: Get user info
name = input("👤 Git username: ")
email = input("📧 Git email: ")
key_name = input("🔐 SSH key name (no spaces): ")

# Step 2: Ask for config scope
scope = input("🌍 Do you want to configure Git globally or locally? (global/local): ").strip().lower()

# Step 3: Handle local setup if needed
if scope == "local":
    path = input("📁 Enter the path you want to configure Git in: ").strip()
    project_path = os.path.expanduser(path)
    os.chdir(project_path)
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"])
elif scope != "global":
    print("❌ Invalid input. Choose 'global' or 'local'.")
    exit()

# Step 4: Set config scope flag
config_args = ["git", "config"]
if scope == "global":
    config_args.append("--global")

# Step 5: Generate SSH key
ssh_path = f"~/.ssh/{key_name}"
ssh_path_expanded = os.path.expanduser(ssh_path)

print("🔐 Generating SSH key...")
subprocess.run([
    "ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email,
    "-f", ssh_path_expanded,
    "-N", ""
])

# Step 6: Set Git user config
print("🛠️ Setting Git config...")
subprocess.run(config_args + ["user.name", name])
subprocess.run(config_args + ["user.email", email])

# Step 7: Set local SSH command if local
if scope == "local":
    subprocess.run(["git", "config", "core.sshCommand", f"ssh -i {ssh_path_expanded} -F /dev/null"])

# Step 8: Start SSH agent & add the key
print("🚀 Adding key to SSH agent...")
subprocess.run("eval $(ssh-agent -s)", shell=True)
subprocess.run(["ssh-add", ssh_path_expanded])

# Step 9: Copy key to clipboard depending on OS
print("📋 Public SSH Key:")
pub_key_path = f"{ssh_path_expanded}.pub"
with open(pub_key_path, "r") as pubkey_file:
    public_key = pubkey_file.read()
    print(public_key)

    os_type = platform.system().lower()

    print("📎 Copying SSH key to clipboard...")

    try:
        if "linux" in os_type:
            subprocess.run("xclip -version", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run(f"echo '{public_key}' | xclip -selection clipboard", shell=True)
        elif "darwin" in os_type:  # macOS
            subprocess.run(f"echo '{public_key}' | pbcopy", shell=True)
        elif "windows" in os_type:
            subprocess.run("clip", input=public_key.encode(), shell=True)
        else:
            print("⚠️ Unknown OS. Couldn’t copy to clipboard.")
    except Exception as e:
        print("❌ Clipboard copy failed:", e)

print("\n✅ All done! SSH key printed above & copied to clipboard (if supported). Paste it into your GitHub SSH settings.")
