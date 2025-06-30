import os
import platform
import subprocess
import shutil

def run_clipboard(command, input_text=None):
    try:
        result = subprocess.run(
            command,
            input=input_text.encode() if input_text else None,
            shell=True
        )
        return result.returncode == 0
    except Exception:
        return False

# User inputs
name = input("Git username: ")
email = input("Git email: ")
key_name = input("SSH key name (no spaces): ")
scope = input("Configure Git globally or locally? (global/local): ").strip().lower()

# Path handling for local setup
if scope == "local":
    path = input("Enter folder path to configure Git in: ").strip()
    project_path = os.path.expanduser(path)
    if not os.path.exists(project_path):
        if input("Path doesn't exist. Create it? (y/n): ").strip().lower() == "y":
            os.makedirs(project_path)
            print(f"Created: {project_path}")
        else:
            print("Canceled.")
            exit()
    os.chdir(project_path)
    if not os.path.isdir(".git"):
        subprocess.run(["git", "init"])
elif scope != "global":
    print("Invalid option. Choose 'global' or 'local'.")
    exit()

# Git config args
config_args = ["git", "config"]
if scope == "global":
    config_args.append("--global")

# Generate SSH key
ssh_path = os.path.expanduser(f"~/.ssh/{key_name}")
pub_key_path = ssh_path + ".pub"
if os.path.exists(ssh_path) or os.path.exists(pub_key_path):
    if input("SSH key exists. Overwrite? (y/n): ").strip().lower() != "y":
        print("Canceled.")
        exit()
    os.remove(ssh_path)
    os.remove(pub_key_path)

subprocess.run([
    "ssh-keygen", "-t", "rsa", "-b", "4096", "-C", email,
    "-f", ssh_path, "-N", ""
])

# Git config
subprocess.run(config_args + ["user.name", name])
subprocess.run(config_args + ["user.email", email])
if scope == "local":
    subprocess.run(["git", "config", "core.sshCommand", f"ssh -i {ssh_path} -F /dev/null"])

# Start ssh-agent and add key
subprocess.run("eval $(ssh-agent -s)", shell=True)
os_type = platform.system().lower()

if "darwin" in os_type:
    subprocess.run(["ssh-add", "--apple-use-keychain", ssh_path])
elif "windows" in os_type:
    subprocess.run(["ssh-add", ssh_path])
else:
    subprocess.run(["ssh-add", ssh_path])
    persist = input("SSH key won't persist after reboot. Auto-load on terminal start? (y/n): ").strip().lower()
    if persist == "y":
        shell_rc = "~/.zshrc" if os.environ.get("SHELL", "").endswith("zsh") else "~/.bashrc"
        rc_path = os.path.expanduser(shell_rc)
        with open(rc_path, "a") as f:
            f.write(f"\n# Auto-load SSH key\n")
            f.write('eval "$(ssh-agent -s)"\n')
            f.write(f"ssh-add {ssh_path}\n")
        print(f"Added SSH auto-load to {rc_path}")

# Show SSH key
with open(pub_key_path, "r") as f:
    public_key = f.read()
print("\nYour SSH Public Key:\n" + public_key)

# Clipboard copy
print("\nTrying to copy SSH key to clipboard...")
clipboard_done = False

try:
    if "linux" in os_type:
        wayland = "wayland" in os.environ.get("XDG_SESSION_TYPE", "")
        tool = "wl-copy" if wayland else "xclip"
        if not shutil.which(tool):
            if shutil.which("sudo"):
                subprocess.run(["sudo", "apt", "install", "-y", "wl-clipboard" if wayland else "xclip"])
        if tool == "wl-copy":
            clipboard_done = run_clipboard(f"echo '{public_key}' | wl-copy")
        else:
            clipboard_done = run_clipboard(f"echo '{public_key}' | xclip -selection clipboard")
    elif "darwin" in os_type:
        clipboard_done = run_clipboard(f"echo '{public_key}' | pbcopy")
    elif "windows" in os_type:
        clipboard_done = run_clipboard("clip", input_text=public_key)
except Exception:
    pass

if clipboard_done:
    print("SSH key copied to clipboard.")
else:
    print("Clipboard copy failed or unsupported. Copy it manually.")

print("\nDone. Paste the key in your GitHub SSH settings.")
