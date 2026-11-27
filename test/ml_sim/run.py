import argparse
import logging
import tkinter as tk

from sim_gui import SimulatorGUI


def main():
    parser = argparse.ArgumentParser(description="Run the Beryllium ML unit simulator.")
    parser.add_argument(
        "port",
        nargs="?",
        help="serial port to preselect in the simulator window",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    root = tk.Tk()
    SimulatorGUI(root, initial_port=args.port)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
