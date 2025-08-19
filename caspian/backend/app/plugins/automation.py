import subprocess
import sys
import os

def register(action: str, arg: str = None) -> str:
    """
    Run a system action: open app, run script, or execute a command.
    Allowed actions: 'open', 'run', 'command'.
    arg: path to app/script or command string.
    """
    if action == "open":
        if not arg:
            return "Please specify an app or file to open."
        try:
            if sys.platform.startswith("win"):
                os.startfile(arg)
            elif sys.platform.startswith("darwin"):
                subprocess.Popen(["open", arg])
            else:
                subprocess.Popen(["xdg-open", arg])
            return f"Opened {arg}."
        except Exception as e:
            return f"Failed to open {arg}: {e}"
    elif action == "run":
        if not arg:
            return "Please specify a script to run."
        try:
            result = subprocess.run([sys.executable, arg], capture_output=True, text=True, timeout=60)
            return f"Script output:\n{result.stdout or result.stderr}"
        except Exception as e:
            return f"Failed to run script: {e}"
    elif action == "command":
        if not arg:
            return "Please specify a command to execute."
        try:
            result = subprocess.run(arg, shell=True, capture_output=True, text=True, timeout=60)
            return f"Command output:\n{result.stdout or result.stderr}"
        except Exception as e:
            return f"Failed to execute command: {e}"
    else:
        return "Unknown action. Use 'open', 'run', or 'command'."
