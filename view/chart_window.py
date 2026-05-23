import tkinter as tk
from datetime import date
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ChartWindow(tk.Toplevel):
    """Modal window with two matplotlib charts: status distribution and overdue analysis."""

    def __init__(self, parent, board):
        """Open the chart window as a modal over the given parent."""
        super().__init__(parent)
        self._board = board
        self.title("Charts")
        self.geometry("1100x520")
        self.minsize(700, 400)
        self.configure(bg="#0F172A")
        self.grab_set()
        self._build()

    def _build(self):
        fig = Figure(figsize=(12, 5), facecolor="#0F172A")
        fig.subplots_adjust(left=0.05, right=0.96, top=0.88, bottom=0.18, wspace=0.45)

        ax1 = fig.add_subplot(1, 2, 1)
        ax2 = fig.add_subplot(1, 2, 2)

        self._draw_status_pie(ax1)
        self._draw_overdue_bars(ax2)

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

    # ── Chart 1 ──────────────────────────────────────────────────────

    def _draw_status_pie(self, ax):
        """Pie chart showing how many items are in each status."""
        board = self._board
        counts = {s.label: 0 for s in board.statuses}
        for item in board.all_items():
            status = board.get_status(item.status_id)
            if status:
                counts[status.label] += 1

        labels = [k for k, v in counts.items() if v > 0]
        values = [v for k, v in counts.items() if v > 0]

        ax.set_facecolor("#1E293B")
        ax.set_title("Items per Status", color="#F8FAFC", fontsize=13, pad=14)

        if not values:
            ax.text(0.5, 0.5, "No items on board", ha="center", va="center",
                    color="#94A3B8", fontsize=11, transform=ax.transAxes)
            return

        palette = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
            "#8B5CF6", "#EC4899", "#06B6D4", "#84CC16",
        ]
        colors = [palette[i % len(palette)] for i in range(len(labels))]

        wedges, texts, autotexts = ax.pie(
            values,
            labels=labels,
            autopct="%1.0f%%",
            colors=colors,
            startangle=90,
            textprops={"color": "#F8FAFC", "fontsize": 9},
            wedgeprops={"linewidth": 2, "edgecolor": "#0F172A"},
        )
        for at in autotexts:
            at.set_color("#0F172A")
            at.set_fontweight("bold")
            at.set_fontsize(8)

    # ── Chart 2 ──────────────────────────────────────────────────────

    def _draw_overdue_bars(self, ax):
        """Horizontal bar chart: days overdue (red) or days remaining (green) for open items."""
        board = self._board
        today = date.today()

        done_keywords = ("done", "complete", "finish", "closed", "close", "shipped", "resolved")
        done_ids = {
            s.id for s in board.statuses
            if any(kw in s.label.lower() for kw in done_keywords)
        }

        entries = []
        for item in board.all_items():
            if item.status_id in done_ids or not item.due_date:
                continue
            days = (item.due_date - today).days
            entries.append((item.title, days))

        ax.set_facecolor("#1E293B")
        ax.set_title("Overdue / Time Left (open items with due date)",
                     color="#F8FAFC", fontsize=11, pad=14)

        if not entries:
            ax.text(0.5, 0.5, "No open items\nwith due dates set",
                    ha="center", va="center", color="#94A3B8",
                    fontsize=11, transform=ax.transAxes, multialignment="center")
            ax.tick_params(colors="#94A3B8")
            return

        entries.sort(key=lambda x: x[1])
        titles = [t[:24] + ("…" if len(t) > 24 else "") for t, _ in entries]
        values = [v for _, v in entries]
        colors = ["#EF4444" if v < 0 else "#10B981" for v in values]

        y_pos = list(range(len(titles)))
        bars = ax.barh(y_pos, values, color=colors, edgecolor="#0F172A",
                       linewidth=0.8, height=0.6)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(titles, color="#F8FAFC", fontsize=8)
        ax.axvline(0, color="#94A3B8", linewidth=1.2, linestyle="--")
        ax.set_xlabel("Days  (negative = overdue,  positive = days left)",
                      color="#94A3B8", fontsize=8)

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#334155")
        ax.tick_params(axis="x", colors="#94A3B8", labelsize=8)
        ax.tick_params(axis="y", colors="#94A3B8")

        for bar, val in zip(bars, values):
            offset = -2 if val < 0 else 2
            ha = "right" if val < 0 else "left"
            label = f"{abs(val)}d overdue" if val < 0 else f"{val}d left"
            ax.text(
                bar.get_width() + offset,
                bar.get_y() + bar.get_height() / 2,
                label, va="center", ha=ha, color="#F8FAFC", fontsize=7,
            )
