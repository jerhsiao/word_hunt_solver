import tkinter as tk
from tkinter import ttk
import requests
from pathlib import Path
from dataclasses import dataclass

@dataclass
class WordInfo:
    word: str
    path: list  # List of (row, col) tuples

class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class Trie:
    def __init__(self):
        self.root = TrieNode()
    def insert(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_end = True
    def is_prefix(self, prefix):
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return True
    def is_word(self, word):
        node = self.root
        for ch in word:
            if ch not in node.children:
                return False
            node = node.children[ch]
        return node.is_end

class WordHuntSolver:
    def __init__(self):
        self.score_lookup = {
            3: 100, 4: 400, 5: 800, 6: 1400, 7: 1800,
            8: 2200, 9: 2600, 10: 3000, 11: 3400, 12: 3800,
            13: 4200, 14: 4600, 15: 5000,
        }
        self.dict_path = Path("words_alpha.txt")
        if not self.dict_path.exists():
            url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
            r = requests.get(url)
            with open(self.dict_path, "wb") as f:
                f.write(r.content)
        
        self.trie = Trie()
        with open(self.dict_path, "r") as f:
            for word in f:
                w = word.strip().upper()
                if 3 <= len(w) <= 15:
                    self.trie.insert(w)
        
        self.directions = [(0,1),(1,1),(1,0),(1,-1),
                           (0,-1),(-1,-1),(-1,0),(-1,1)]
        self.board = []
        self.found_words = set()
        self.word_info_map = {}

    def solve(self, letters):
        self.board = [list(letters[i:i+4]) for i in range(0,16,4)]
        self.found_words.clear()
        self.word_info_map.clear()

        for r in range(4):
            for c in range(4):
                self._dfs(r, c, "", [], set())

        return sorted(self.found_words, key=lambda w: (-len(w), w))

    def _dfs(self, r, c, current_word, path, visited):
        if (r, c) in visited:
            return
        current_word += self.board[r][c]
        if len(current_word) > 15:
            return
        
        path.append((r, c))
        visited.add((r, c))

        if not self.trie.is_prefix(current_word):
            path.pop()
            visited.remove((r, c))
            return

        if len(current_word) >= 3 and self.trie.is_word(current_word):
            if current_word not in self.word_info_map:
                self.found_words.add(current_word)
                self.word_info_map[current_word] = WordInfo(
                    word=current_word, path=path.copy()
                )

        for dr, dc in self.directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 4 and 0 <= nc < 4:
                self._dfs(nr, nc, current_word, path, visited)

        path.pop()
        visited.remove((r, c))

    def get_score(self, length):
        return self.score_lookup.get(length, 0)

class WordHuntApp:
    def __init__(self):
        self.solver = WordHuntSolver()
        self.window = tk.Tk()
        self.window.title("Word Hunt Solver")
        self.window.geometry("600x800")

        self.current_highlight = []
        self.path_lines = []
        self.entry_centers = {}

        self.default_bg = {}

        main_frame = ttk.Frame(self.window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Enter letters from left to right, top to bottom:")\
            .pack()

        self.grid_frame = ttk.Frame(main_frame)
        self.grid_frame.pack()

        # Use a canvas for drawing the connecting lines
        self.canvas = tk.Canvas(self.grid_frame, highlightthickness=0)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self.entries = []
        for r in range(4):
            row_entries = []
            for c in range(4):
                e = tk.Entry(
                    self.grid_frame, width=3, font=('Arial', 20), justify='center'
                )
                e.grid(row=r, column=c, padx=5, pady=5)

                self.default_bg[e] = e.cget("bg")
                e.bind("<KeyRelease>", lambda evt, rr=r, cc=c: self.on_key_release(evt, rr, cc))
                row_entries.append(e)
            self.entries.append(row_entries)

        ttk.Button(main_frame, text="Find Words", command=self.solve)\
            .pack(pady=10)

        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(results_frame, font=('Arial', 12), width=50, height=20)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(results_frame, command=self.results_text.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.configure(yscrollcommand=sb.set)

        # Configure clickable text tag
        self.results_text.tag_configure("word", underline=True)
        self.results_text.tag_bind("word", "<Button-1>", self.word_clicked)

        self.window.after(100, self.capture_entry_centers)

    def capture_entry_centers(self):
        """Measure widget positions to know where to draw lines."""
        self.grid_frame.update_idletasks()
        for r in range(4):
            for c in range(4):
                e = self.entries[r][c]
                x = e.winfo_x() + e.winfo_width() // 2
                y = e.winfo_y() + e.winfo_height() // 2
                self.entry_centers[(r,c)] = (x, y)


    def on_key_release(self, event, row, col):
        val = self.entries[row][col].get().upper()
        if val:
            self.entries[row][col].delete(0, tk.END)
            self.entries[row][col].insert(0, val[-1])
            nr = row + (col + 1)//4
            nc = (col + 1) % 4
            if nr < 4:
                self.entries[nr][nc].focus()

    def clear_highlights(self):
        for e in self.current_highlight:
            e.config(bg=self.default_bg[e])
        self.current_highlight.clear()

        for line_id in self.path_lines:
            self.canvas.delete(line_id)
        self.path_lines.clear()

    def word_clicked(self, event):
        idx = self.results_text.index(f"@{event.x},{event.y}")
        line_start = f"{idx} linestart"
        line_end = f"{idx} lineend"
        clicked_line = self.results_text.get(line_start, line_end).strip()

        if "Letter Words" in clicked_line or "Total Score" in clicked_line:
            return

        self.clear_highlights()
        info = self.solver.word_info_map.get(clicked_line)
        if not info:
            return

        path = info.path
        path_len = len(path)
        if path_len == 0:
            return

        # Start: dark green (#006400), End: a reasonably lighter green (#60c060)
        start_rgb = (0x00, 0x64, 0x00)  # #006400
        end_rgb   = (0x60, 0xc0, 0x60)  # #60c060

        steps = max(path_len - 1, 1)

        # Generate a gradient from dark to lighter green
        path_colors = []
        for i, (r, c) in enumerate(path):
            t = i / steps  # fraction from start to end
            R = int(start_rgb[0] + t * (end_rgb[0] - start_rgb[0]))
            G = int(start_rgb[1] + t * (end_rgb[1] - start_rgb[1]))
            B = int(start_rgb[2] + t * (end_rgb[2] - start_rgb[2]))
            color_hex = f"#{R:02x}{G:02x}{B:02x}"
            self.entries[r][c].config(bg=color_hex)
            self.current_highlight.append(self.entries[r][c])
            path_colors.append(color_hex)

        # Draw arrow lines using the color of the destination square
        for i in range(path_len - 1):
            (r1, c1) = path[i]
            (r2, c2) = path[i+1]
            x1, y1 = self.entry_centers.get((r1, c1), (0,0))
            x2, y2 = self.entry_centers.get((r2, c2), (0,0))
            line_color = path_colors[i+1]
            line_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=line_color, width=2, arrow=tk.LAST
            )
            self.path_lines.append(line_id)

    def solve(self):
        self.clear_highlights()
        letters = []
        for r in range(4):
            for c in range(4):
                ch = self.entries[r][c].get().upper()
                if not ch:
                    self.results_text.delete("1.0", tk.END)
                    self.results_text.insert(tk.END, "Please fill in all letters.")
                    return
                letters.append(ch)

        found = self.solver.solve("".join(letters))
        self.results_text.delete("1.0", tk.END)

        total_score = 0
        words_by_len = {}
        for w in found:
            ln = len(w)
            words_by_len.setdefault(ln, []).append(w)

        for ln in sorted(words_by_len.keys(), reverse=True):
            pts = self.solver.get_score(ln)
            self.results_text.insert(tk.END, f"\n{ln} Letter Words ({pts} points per word):\n")
            for w in sorted(words_by_len[ln]):
                total_score += pts
                self.results_text.insert(tk.END, w + "\n", "word")

        self.results_text.insert(tk.END, f"\nTotal Score: {total_score} points")
        self.results_text.see("1.0")

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    WordHuntApp().run()
