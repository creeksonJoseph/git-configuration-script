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

# Check if key exists
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

# Step 9: Show and optionally copy the public key
print("Your SSH Public Key:")
with open(pub_key_path, "r") as pubkey_file:
    public_key = pubkey_file.read()
    print(public_key)

os_type = platform.system().lower()
clipboard_copied = False

print("Checking for clipboard tool...")

try:
    if "linux" in os_type:
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        wayland_display = os.environ.get("WAYLAND_DISPLAY")
        is_wayland = "wayland" in session_type or wayland_display

        if is_wayland:
            print("Wayland session detected. Using wl-copy.")
            if shutil.which("wl-copy"):
                copied = try_clipboard_copy(f"echo '{public_key}' | wl-copy")
                if copied:
                    clipboard_copied = True
                    print("SSH key copied using wl-copy.")
                else:
                    print("Clipboard command ran but may not have copied. Paste manually if needed.")
            else:
                print("wl-copy not found. Attempting to install wl-clipboard...")
                try:
                    if hasattr(os, "geteuid") and os.geteuid() == 0:
                        subprocess.run(["apt", "update"], check=True)
                        subprocess.run(["apt", "install", "-y", "wl-clipboard"], check=True)
                    elif shutil.which("sudo"):
                        subprocess.run(["sudo", "apt", "update"], check=True)
                        subprocess.run(["sudo", "apt", "install", "-y", "wl-clipboard"], check=True)
                    else:
                        raise PermissionError("No sudo/root access")

                    if shutil.which("wl-copy"):
                        copied = try_clipboard_copy(f"echo '{public_key}' | wl-copy")
                        if copied:
                            clipboard_copied = True
                            print("SSH key copied using wl-copy after install.")
                        else:
                            print("Clipboard command ran but may not have copied. Paste manually if needed.")
                except Exception as e:
                    print("Failed to install wl-clipboard:", e)

        else:
            print("X11 session detected or fallback mode. Using xclip.")
            if shutil.which("xclip"):
                copied = try_clipboard_copy(f"echo '{public_key}' | xclip -selection clipboard")
                if copied:
                    clipboard_copied = True
                    print("SSH key copied using xclip.")
                else:
                    print("Clipboard command ran but may not have copied. Paste manually if needed.")
            else:
                print("xclip not found. Attempting to install it...")
                try:
                    if hasattr(os, "geteuid") and os.geteuid() == 0:
                        subprocess.run(["apt", "update"], check=True)
                        subprocess.run(["apt", "install", "-y", "xclip"], check=True)
                    elif shutil.which("sudo"):
                        subprocess.run(["sudo", "apt", "update"], check=True)
                        subprocess.run(["sudo", "apt", "install", "-y", "xclip"], check=True)
                    else:
                        raise PermissionError("No sudo/root access")

                    if shutil.which("xclip"):
                        copied = try_clipboard_copy(f"echo '{public_key}' | xclip -selection clipboard")
                        if copied:
                            clipboard_copied = True
                            print("SSH key copied using xclip after install.")
                        else:
                            print("Clipboard command ran but may not have copied. Paste manually if needed.")
                except Exception as e:
                    print("Failed to install xclip:", e)

    elif "darwin" in os_type:
        if shutil.which("pbcopy"):
            copied = try_clipboard_copy(f"echo '{public_key}' | pbcopy")
            if copied:
                clipboard_copied = True
                print("SSH key copied using pbcopy.")
            else:
                print("Clipboard command ran but may not have copied. Paste manually if needed.")
        else:
            print("pbcopy not found on macOS.")

    elif "windows" in os_type:
        if shutil.which("clip"):
            copied = try_clipboard_copy("clip", input_text=public_key)
            if copied:
                clipboard_copied = True
                print("SSH key copied using clip.")
            else:
                print("Clipboard command ran but may not have copied. Paste manually if needed.")
        else:
            print("clip command not found on Windows.")

    else:
        print("Unknown OS. Clipboard copy skipped.")

except Exception as e:
    print("Clipboard copy failed:", e)

if not clipboard_copied:
    print("You can still copy the SSH key manually from above.")

print("Done. SSH key is printed above and copied to clipboard (if supported). Paste it into your GitHub SSH settings.")
