import threading
import time
import tkinter as tk
from datetime import datetime

# === Configuration ===
DIRECTIONS = ['N', 'E', 'S', 'W']
NUM_INTERSECTIONS = 2
SIGNAL_TIMINGS = {'green': 5, 'yellow': 2, 'red': 5}
EMERGENCY_GREEN_DURATION = 7
LOG_FILE = r'C:\Users\meher\Desktop\signal_log.txt'  # CHANGE THIS TO YOUR USERNAME


# === Logging Function ===
def log_event(intersection_id, direction, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_line = f"{timestamp} | Intersection {intersection_id} | Direction {direction} | {message}"
    print(log_line)
    with open(LOG_FILE, 'a') as f:
        f.write(log_line + '\n')


# === Traffic Signal Class for Each Intersection ===
class TrafficSignal(threading.Thread):
    def __init__(self, intersection_id):
        super().__init__()
        self.intersection_id = intersection_id
        self.states = {d: 'red' for d in DIRECTIONS}
        self.running = True
        self.emergency_lock = threading.Lock()
        self.emergency_direction = None
        self.gui_callback = None

    
    def run(self):
     while self.running:
        if self.emergency_direction:
            self.handle_emergency(self.emergency_direction)
            self.emergency_direction = None
            continue

        for direction in DIRECTIONS:
            if self.emergency_direction:
                break  # interrupt and handle immediately

            self.set_all_red()
            self.set_state(direction, 'green')
            if self.sleep_with_emergency_check(SIGNAL_TIMINGS['green']):
                continue  # emergency occurred, handle on next loop

            self.set_state(direction, 'yellow')
            if self.sleep_with_emergency_check(SIGNAL_TIMINGS['yellow']):
                continue

            self.set_state(direction, 'red')
            if self.sleep_with_emergency_check(SIGNAL_TIMINGS['red']):
                continue


    def set_state(self, direction, state):
        with self.emergency_lock:
            self.states[direction] = state
        if self.gui_callback:
            self.gui_callback()
    
    def set_all_red(self):
        with self.emergency_lock:
            for d in DIRECTIONS:
                self.states[d] = 'red'
        if self.gui_callback:
            self.gui_callback()

    def get_states(self):
        with self.emergency_lock:
            return self.states.copy()

    def trigger_emergency(self, direction):
        self.emergency_direction = direction

    def handle_emergency(self, direction):
    # Step 1: Check if any other direction is currently green
     active_green = None
     with self.emergency_lock:
        for d, state in self.states.items():
            if state == 'green' and d != direction:
                active_green = d
                break

    # Step 2: If there’s an ongoing green, transition it to yellow, then red
     if active_green:
        log_event(self.intersection_id, active_green, "INTERRUPTED BY EMERGENCY – Switching to YELLOW")
        self.set_state(active_green, 'yellow')
        time.sleep(1)  # 1 second yellow before red
        self.set_state(active_green, 'red')
        log_event(self.intersection_id, active_green, "YELLOW COMPLETE – Switching to RED")

    # Step 3: Start emergency green cycle
     self.set_all_red()
     log_event(self.intersection_id, direction, "EMERGENCY DETECTED – Switching to GREEN")
     self.set_state(direction, 'green')
     time.sleep(EMERGENCY_GREEN_DURATION)
     self.set_state(direction, 'red')
     log_event(self.intersection_id, direction, "EMERGENCY ENDED – Switching to RED")

    def sleep_with_emergency_check(self, total_duration):
     """Sleep in small steps and return True if emergency was detected."""
     slept = 0
     while slept < total_duration:
        time.sleep(0.2)
        slept += 0.2
        if self.emergency_direction:
            return True
     return False



# === GUI Class ===
class TrafficGUI:
    def __init__(self, root, signals):
        self.root = root
        self.signals = signals
        self.canvas_refs = {}
        self.setup_ui()
        self.update_gui()

    def setup_ui(self):
        self.root.title("Multi-Intersection Traffic Signal System")
        tk.Label(self.root, text="Emergency Traffic Control", font=('Arial', 16, 'bold')).pack(pady=10)

        container = tk.Frame(self.root)
        container.pack()

        for i, signal in enumerate(self.signals, start=1):
            frame = tk.LabelFrame(container, text=f"Intersection {i}", padx=10, pady=10, font=('Arial', 12))
            frame.grid(row=0, column=i-1, padx=10, pady=5)

            for d in DIRECTIONS:
                sig_frame = tk.Frame(frame, pady=5)
                sig_frame.pack()

                label = tk.Label(sig_frame, text=f"Direction {d}", font=('Arial', 10))
                label.pack()

                canvas = tk.Canvas(sig_frame, width=60, height=180, bg='white')
                canvas.pack()
                r = canvas.create_oval(10, 10, 50, 50, fill='gray')
                y = canvas.create_oval(10, 65, 50, 105, fill='gray')
                g = canvas.create_oval(10, 120, 50, 160, fill='gray')
                self.canvas_refs[(i, d)] = {'canvas': canvas, 'red': r, 'yellow': y, 'green': g}

                btn = tk.Button(sig_frame, text=f"Trigger Emergency", command=lambda inter=i, dir=d: self.signals[inter-1].trigger_emergency(dir))
                btn.pack(pady=2)

    def update_gui(self):
        for i, signal in enumerate(self.signals, start=1):
            states = signal.get_states()
            for d in DIRECTIONS:
                ref = self.canvas_refs[(i, d)]
                ref['canvas'].itemconfig(ref['red'], fill='gray')
                ref['canvas'].itemconfig(ref['yellow'], fill='gray')
                ref['canvas'].itemconfig(ref['green'], fill='gray')

                state = states[d]
                if state == 'red':
                    ref['canvas'].itemconfig(ref['red'], fill='red')
                elif state == 'yellow':
                    ref['canvas'].itemconfig(ref['yellow'], fill='yellow')
                elif state == 'green':
                    ref['canvas'].itemconfig(ref['green'], fill='green')

        self.root.after(500, self.update_gui)


# === Main ===
def main():
    root = tk.Tk()
    signals = []

    for i in range(1, NUM_INTERSECTIONS + 1):
        ts = TrafficSignal(i)
        signals.append(ts)

    gui = TrafficGUI(root, signals)

    for ts in signals:
        ts.gui_callback = gui.update_gui
        ts.start()

    root.mainloop()

    for ts in signals:
        ts.running = False
        ts.join()


if __name__ == '__main__':
    main()
