import os
import platform
import subprocess
import shutil

# Step 1: Get user info
name = input("Git username: ")
email = input("Git email: ")
key_name = input("SSH key name (no spaces): ")

# Step 2: Ask for config scope
scope = input("Do you want to configure Git globally or locally? (global/local): ").strip().lower()

# Step 3: Handle local setup if needed
if scope == "local":
    path = input("Enter the path you want to configure Git in: ").strip()
    project_path = os.path.expanduser(path)

    if not os.path.exists(project_path):
        print("Error: Path does not exist.")
        exit()

    os.chdir(project_path)

    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"])
elif scope != "global":
    print("Invalid input. Choose 'global' or 'local'.")
    exit()

# Step 4: Set config scope flag
config_args = ["git", "config"]
if scope == "global":
    config_args.append("--global")

# Step 5: Generate SSH key
ssh_path = f"~/.ssh/{key_name}"
ssh_path_expanded = os.path.expanduser(ssh_path)
pub_key_path = f"{ssh_path_expanded}.pub"

# Check if either private or public key already exists
if os.path.exists(ssh_path_expanded) or os.path.exists(pub_key_path):
    print("Warning: SSH key with that name already exists.")
    choice = input("Do you want to overwrite it? (y/n): ").strip().lower()
    if choice == "y":
        try:
            if os.path.exists(ssh_path_expanded):
                os.remove(ssh_path_expanded)
            if os.path.exists(pub_key_path):
                os.remove(pub_key_path)
            print("Old key deleted.")
        except Exception as e:
            print("Failed to delete existing keys:", e)
            exit()
    else:
        print("Canceled. Use a different SSH key name.")
        exit()

print("Generating SSH key...")
subprocess.run([
    "ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email,
    "-f", ssh_path_expanded,
    "-N", ""
])

# Step 6: Set Git user config
print("Setting Git config...")
subprocess.run(config_args + ["user.name", name])
subprocess.run(config_args + ["user.email", email])

# Step 7: Set local SSH command if local
if scope == "local":
    subprocess.run(["git", "config", "core.sshCommand", f"ssh -i {ssh_path_expanded} -F /dev/null"])

# Step 8: Start SSH agent & add the key
print("Starting SSH agent and adding key...")
subprocess.run("eval $(ssh-agent -s)", shell=True)
subprocess.run(["ssh-add", ssh_path_expanded])

# Step 9: Copy key to clipboard depending on OS
print("Your SSH Public Key:")
with open(pub_key_path, "r") as pubkey_file:
    public_key = pubkey_file.read()
    print(public_key)

os_type = platform.system().lower()
clipboard_copied = False

print("Checking for clipboard tool...")

try:
    if "linux" in os_type:
        if shutil.which("xclip"):
            subprocess.run(f"echo '{public_key}' | xclip -selection clipboard", shell=True)
            clipboard_copied = True
            print("SSH key copied using xclip.")
        elif shutil.which("wl-copy"):
            subprocess.run(f"echo '{public_key}' | wl-copy", shell=True)
            clipboard_copied = True
            print("SSH key copied using wl-copy.")
        else:
            print("No clipboard tool found. Attempting to install xclip...")

            try:
                if hasattr(os, "geteuid") and os.geteuid() == 0:
                    subprocess.run(["apt", "update"], check=True)
                    subprocess.run(["apt", "install", "-y", "xclip"], check=True)
                elif shutil.which("sudo"):
                    subprocess.run(["sudo", "apt", "update"], check=True)
                    subprocess.run(["sudo", "apt", "install", "-y", "xclip"], check=True)
                else:
                    print("Cannot install xclip — 'sudo' is not available and you're not root.")
                    print("Please install it manually: apt install xclip")
                    raise PermissionError("Insufficient privileges")

                # Try copying again
                if shutil.which("xclip"):
                    subprocess.run(f"echo '{public_key}' | xclip -selection clipboard", shell=True)
                    clipboard_copied = True
                    print("SSH key copied using installed xclip.")
                else:
                    print("xclip not found even after install.")

            except Exception as e:
                print("Clipboard install or copy failed:", e)

    elif "darwin" in os_type:
        if shutil.which("pbcopy"):
            subprocess.run(f"echo '{public_key}' | pbcopy", shell=True)
            clipboard_copied = True
            print("SSH key copied using pbcopy.")
        else:
            print("pbcopy not found on macOS.")

    elif "windows" in os_type:
        if shutil.which("clip"):
            subprocess.run("clip", input=public_key.encode(), shell=True)
            clipboard_copied = True
            print("SSH key copied using clip.")
        else:
            print("clip command not found on Windows.")

    else:
        print("Unknown OS. Clipboard copy skipped.")

except Exception as e:
    print("Clipboard copy failed:", e)

if not clipboard_copied:
    print("You can still copy the SSH key manually from above.")

print("Done. SSH key is printed above and copied to clipboard (if supported). Paste it into your GitHub SSH settings.")
