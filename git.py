import os
import platform
import subprocess
import shutil

def try_clipboard_copy(command, input_text=None, shell=True):
    try:
        result = subprocess.run(command, input=input_text.encode() if input_text else None, shell=shell)
        return result.returncode == 0
    except Exception:
        return False

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
        print("That folder doesn't exist.")
        create = input("Do you want to create it? (y/n): ").strip().lower()
        if create == "y":
            try:
                os.makedirs(project_path)
                print(f"Folder created at {project_path}")
            except Exception as e:
                print("Failed to create folder:", e)
                exit()
        else:
            print("Canceled. Provide a valid existing path next time.")
            exit()

    try:
        os.chdir(project_path)
    except Exception as e:
        print("Failed to enter directory:", e)
        exit()

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

if os.path.exists(ssh_path_expanded) or os.path.exists(pub_key_path):
    print("Warning: SSH key with that name already exists.")
    choice = input("Do you want to overwrite it? (y/n): ").strip().lower()
    if choice == "y":
        try:
            os.remove(ssh_path_expanded)
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

# Step 8: Start SSH agent & add key
print("Starting SSH agent and adding key...")
subprocess.run("eval $(ssh-agent -s)", shell=True)

os_type = platform.system().lower()
use_keychain = False
clipboard_copied = False

if "darwin" in os_type:
    # macOS Keychain support
    use_keychain = shutil.which("ssh-add") is not None
    if use_keychain:
        subprocess.run(["ssh-add", "--apple-use-keychain", ssh_path_expanded])
    else:
        subprocess.run(["ssh-add", ssh_path_expanded])
elif "windows" in os_type:
    subprocess.run(["ssh-add", ssh_path_expanded])
else:
    subprocess.run(["ssh-add", ssh_path_expanded])

# Step 8.1: Persist SSH key if needed
if "linux" in os_type:
    print("Note: SSH key won't persist after reboot unless added on shell startup.")
    persist = input("Do you want to auto-load this key on terminal startup? (y/n): ").strip().lower()
    if persist == "y":
        shell_rc = os.path.expanduser("~/.bashrc")
        if os.environ.get("SHELL", "").endswith("zsh"):
            shell_rc = os.path.expanduser("~/.zshrc")

        agent_line = 'eval "$(ssh-agent -s)"\n'
        add_line = f"ssh-add {ssh_path_expanded}\n"

        try:
            with open(shell_rc, "a") as rcfile:
                rcfile.write(f"\n# Auto-load SSH key for Git\n{agent_line}{add_line}")
            print(f"SSH auto-load added to {shell_rc}.")
        except Exception as e:
            print("Failed to write auto-load config:", e)
elif "darwin" in os_type:
    print("macOS detected. Key was added to Keychain using: ssh-add --apple-use-keychain")
elif "windows" in os_type:
    print("Windows detected. OpenSSH agent handles persistence automatically.")

# Step 9: Show public key
print("Your SSH Public Key:")
with open(pub_key_path, "r") as pubkey_file:
    public_key = pubkey_file.read()
    print(public_key)

# Step 10: Copy to clipboard
print("Checking for clipboard tool...")
try:
    if "linux" in os_type:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        is_wayland = "wayland" in session_type or os.environ.get("WAYLAND_DISPLAY")

        if is_wayland:
            if shutil.which("wl-copy"):
                if try_clipboard_copy(f"echo '{public_key}' | wl-copy"):
                    clipboard_copied = True
                    print("SSH key copied using wl-copy.")
            elif shutil.which("sudo"):
                subprocess.run(["sudo", "apt", "install", "-y", "wl-clipboard"], check=True)
        else:
            if shutil.which("xclip"):
                if try_clipboard_copy(f"echo '{public_key}' | xclip -selection clipboard"):
                    clipboard_copied = True
                    print("SSH key copied using xclip.")
            elif shutil.which("sudo"):
                subprocess.run(["sudo", "apt", "install", "-y", "xclip"], check=True)
    elif "darwin" in os_type and shutil.which("pbcopy"):
        if try_clipboard_copy(f"echo '{public_key}' | pbcopy"):
            clipboard_copied = True
            print("SSH key copied using pbcopy.")
    elif "windows" in os_type and shutil.which("clip"):
        if try_clipboard_copy("clip", input_text=public_key):
            clipboard_copied = True
            print("SSH key copied using clip.")
except Exception as e:
    print("Clipboard copy failed:", e)

if not clipboard_copied:
    print("Clipboard may not have worked. Copy the SSH key manually above.")

print("Done. Paste the key into your GitHub SSH settings.")
