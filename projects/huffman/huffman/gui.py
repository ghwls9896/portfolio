"""
gui.py — Huffman Visualizer with:
- Mouse wheel zoom (no Ctrl needed)
- Drag to move canvas
- Auto-spaced Huffman tree layout (no overlapping)
- Dark themed UI & Entry fields
"""

import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from .fileio import compress_file, decompress_file
from .stats import compute_stats
from .tree import build_huffman_tree, build_codes
from .freq import build_freq_table


# ----------------- THEME -----------------

def set_dark_theme(root):
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except:
        pass

    style.configure(".", background="#222222", foreground="#eeeeee", font=("Segoe UI", 11))
    style.configure("TButton", background="#333333", foreground="#ffffff", padding=6)
    style.map("TButton", background=[("active", "#555555")])
    style.configure("TLabel", background="#222222", foreground="#eeeeee")


# ----------------- ZOOMABLE CANVAS -----------------

class ZoomableCanvas(tk.Canvas):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        self.scale_factor = 1.0
        self.configure(scrollregion=(0, 0, 4000, 4000))

        # Enable drag
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.drag)

        # Mouse wheel zoom (no Ctrl needed)
        self.bind("<MouseWheel>", self.zoom)

    def start_drag(self, event):
        self.scan_mark(event.x, event.y)

    def drag(self, event):
        self.scan_dragto(event.x, event.y, gain=1)

    def zoom(self, event):
        # Zoom in/out
        factor = 1.1 if event.delta > 0 else 0.9
        self.scale_factor *= factor

        self.scale("all", event.x, event.y, factor, factor)
        self.configure(scrollregion=self.bbox("all"))


# ----------------- MAIN GUI -----------------

class HuffmanVisualizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Huffman Coding Visualizer — Zoomable Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg="#222222")

        set_dark_theme(root)

        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.mode_var = tk.StringVar(value="compress")

        self.freq = None
        self.tree_root = None
        self.codes = {}

        self.build_ui()

    # ----------------- UI LAYOUT -----------------

    def build_ui(self):
        pad = {"padx": 10, "pady": 6}

        # ---------------- TOP BAR ----------------
        top = ttk.Frame(self.root)
        top.pack(fill="x", **pad)

        ttk.Label(top, text="Mode: ").pack(side="left")
        ttk.Radiobutton(top, text=" Compress ", value="compress", variable=self.mode_var).pack(side="left")
        ttk.Radiobutton(top, text=" Decompress ", value="decompress", variable=self.mode_var).pack(side="left")

        ttk.Label(top, text=" Input: ").pack(side="left")

        self.in_entry = tk.Entry(top, textvariable=self.input_path,
                                 bg="#333333", fg="#ffffff", insertbackground="white", width=45)
        self.in_entry.pack(side="left")

        ttk.Button(top, text="Browse", command=self.browse_input).pack(side="left", padx=5)

        ttk.Label(top, text=" Output: ").pack(side="left", padx=10)

        self.out_entry = tk.Entry(top, textvariable=self.output_path,
                                  bg="#333333", fg="#ffffff", insertbackground="white", width=45)
        self.out_entry.pack(side="left")

        ttk.Button(top, text="Browse", command=self.browse_output).pack(side="left")

        # ---------------- CENTER ----------------
        center = ttk.Frame(self.root)
        center.pack(fill="both", expand=True, **pad)

        # Canvas + Scrollbars
        canvas_frame = ttk.Frame(center)
        canvas_frame.pack(side="left", fill="both", expand=True)

        self.h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal")
        self.h_scroll.pack(side="bottom", fill="x")

        self.v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical")
        self.v_scroll.pack(side="right", fill="y")

        self.canvas = ZoomableCanvas(canvas_frame, bg="#111111",
                                     xscrollcommand=self.h_scroll.set,
                                     yscrollcommand=self.v_scroll.set)
        self.canvas.pack(fill="both", expand=True)

        self.h_scroll.config(command=self.canvas.xview)
        self.v_scroll.config(command=self.canvas.yview)

        # Right panel (Huffman codes)
        right = ttk.Frame(center)
        right.pack(side="right", fill="y")

        ttk.Label(right, text="Huffman Codes",
                  font=("Segoe UI", 14, "bold")).pack(pady=10)

        self.code_box = tk.Text(right, width=40, height=40,
                                bg="#1b1b1b", fg="#00ff88",
                                font=("Consolas", 10))
        self.code_box.pack(fill="y")

        # ---------------- BOTTOM ----------------
        bottom = ttk.Frame(self.root)
        bottom.pack(fill="x", padx=10, pady=5)

        ttk.Button(bottom, text="▶ Build Huffman Tree",
                   command=self.visualize).pack(side="left", padx=5)

        ttk.Button(bottom, text="▶ Compress / Decompress",
                   command=self.do_process).pack(side="left", padx=5)

        self.log_box = tk.Text(bottom, height=8, bg="#111111",
                               fg="#bbbbbb", font=("Consolas", 10))
        self.log_box.pack(fill="x", expand=True, padx=5)

    # ----------------- FILE HANDLING -----------------

    def browse_input(self):
        p = filedialog.askopenfilename()
        if p:
            self.input_path.set(p)

    def browse_output(self):
        p = filedialog.asksaveasfilename()
        if p:
            self.output_path.set(p)

    # ----------------- LOGGING -----------------

    def log(self, msg):
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")

    # ----------------- HUFFMAN VISUALIZATION -----------------

    def visualize(self):
        """Load file → build tree → auto-layout draw."""
        try:
            data = open(self.input_path.get(), "rb").read()
        except:
            messagebox.showerror("Error", "Cannot read input file.")
            return

        self.freq = build_freq_table(data)
        self.tree_root = build_huffman_tree(self.freq)
        self.codes = build_codes(self.tree_root)

        self.log("✔ Frequency table ready.")
        self.log("✔ Huffman tree built.")
        self.log("✔ Codes generated.")

        self.draw_tree()
        self.update_code_list()

    # ----------------- AUTO-LAYOUT TREE DRAW -----------------

    def draw_tree(self):
        self.canvas.delete("all")
        root = self.tree_root
        if root is None:
            return

        # ---- compute subtree widths ----
        def subtree_width(node):
            if node is None:
                return 0
            if not node.left and not node.right:
                return 120
            return subtree_width(node.left) + subtree_width(node.right) + 80

        width = subtree_width(root)
        start_x = width // 2 + 300
        start_y = 80

        # ---- recursive draw ----
        def draw(node, x, y):
            if node is None:
                return

            lw = subtree_width(node.left)
            rw = subtree_width(node.right)

            # Draw node
            self.canvas.create_oval(x-30, y-30, x+30, y+30,
                                    fill="#333333", outline="#00ffaa", width=2)
            label = f"{node.freq}" if node.byte is None else f"{chr(node.byte)}\n({node.freq})"
            self.canvas.create_text(x, y, text=label,
                                    fill="#00ff88", font=("Segoe UI", 10, "bold"))

            next_y = y + 140

            if node.left:
                child_x = x - rw//2 - 60
                self.canvas.create_line(x, y+30, child_x, next_y-30, fill="#00ffaa")
                draw(node.left, child_x, next_y)

            if node.right:
                child_x = x + lw//2 + 60
                self.canvas.create_line(x, y+30, child_x, next_y-30, fill="#00ffaa")
                draw(node.right, child_x, next_y)

        draw(root, start_x, start_y)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    # ----------------- CODE LIST -----------------

    def update_code_list(self):
        self.code_box.delete("1.0", "end")
        for b, code in sorted(self.codes.items(), key=lambda x: len(x[1])):
            char = chr(b) if 32 <= b <= 126 else "."
            self.code_box.insert("end", f"{char:3} ({b:3}) : {code}\n")

    # ----------------- COMPRESS / DECOMPRESS -----------------

    def do_process(self):
        mode = self.mode_var.get()
        inp = self.input_path.get()
        out = self.output_path.get()

        if not inp or not out:
            messagebox.showerror("Error", "Both input and output are required.")
            return

        def work():
            t0 = time.time()

            if mode == "compress":
                orig, comp, _ = compress_file(inp, out)
                self.log("✔ Compression done.")
            else:
                orig, comp, _ = decompress_file(inp, out)
                self.log("✔ Decompression done.")

            t1 = time.time()
            stats = compute_stats(orig, comp)

            self.log(f"Original: {orig} bytes")
            self.log(f"Compressed: {comp} bytes")
            self.log(f"Compression: {stats['compression_ratio']*100:.2f}%")
            self.log(f"Bits/char: {stats['avg_bits_per_char']:.2f}")
            self.log(f"Time: {(t1-t0)*1000:.2f} ms")

        threading.Thread(target=work).start()


# ----------------- RUN -----------------

def run_gui():
    root = tk.Tk()
    HuffmanVisualizerGUI(root)
    root.mainloop()
