import sys
import os

from gui import CamShowApp

def main():
    app = CamShowApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()
