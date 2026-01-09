"""Run the Claude Pulse tray application."""

import sys
print("Importing tray module...", flush=True)

from tray.main import main

if __name__ == "__main__":
    print("Starting Claude Pulse tray application...", flush=True)
    main()
