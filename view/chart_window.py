import tkinter as tk
from datetime import date
import matplotlib
import matplotlib.ticker
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class ChartWindow(tk.Toplevel):
    """Modal window with three matplotlib charts: status pie, due-date histogram, item age heatmap."""

    def __init__(self, parent, board):
        """Open the chart window as a modal over the given parent."""
        super().__init__(parent)
        self._board = board
        self.title("Charts")
        self.geometry("1600x520")
        self.minsize(1000, 400)
        self.configure(bg="#0F172A")
        self.grab_set()
        self._build()

    def _build(self):
        fig = Figure(figsize=(17, 5), facecolor="#0F172A")
        fig.subplots_adjust(left=0.04, right=0.97, top=0.88, bottom=0.22, wspace=0.45)

        ax1 = fig.add_subplot(1, 3, 1)
        ax2 = fig.add_subplot(1, 3, 2)
        ax3 = fig.add_subplot(1, 3, 3)

        self._draw_status_pie(ax1)
        self._draw_due_date_histogram(ax2)
        self._draw_age_heatmap(ax3)

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

    def _draw_due_date_histogram(self, ax):
        """Bar chart: number of open items due each week (overdue bucket + 8 future weeks)."""
        from datetime import timedelta
        board = self._board
        today = date.today()
        # Monday of the current week
        week_start = today - timedelta(days=today.weekday())

        done_keywords = ("done", "complete", "finish", "closed", "close", "shipped", "resolved")
        done_ids = {
            s.id for s in board.statuses
            if any(kw in s.label.lower() for kw in done_keywords)
        }

        # Buckets: index 0 = overdue, indices 1..8 = weeks ahead
        WEEKS_AHEAD = 8
        counts = [0] * (WEEKS_AHEAD + 1)

        for item in board.all_items():
            if item.status_id in done_ids or not item.due_date:
                continue
            delta = (item.due_date - week_start).days
            if delta < 0:
                counts[0] += 1
            else:
                bucket = delta // 7 + 1
                if bucket <= WEEKS_AHEAD:
                    counts[bucket] += 1
                # items beyond 8 weeks are ignored (not cluttering the view)

        ax.set_facecolor("#1E293B")
        ax.set_title("Upcoming Due Dates (open items)", color="#F8FAFC", fontsize=13, pad=14)

        if sum(counts) == 0:
            ax.text(0.5, 0.5, "No open items\nwith due dates set",
                    ha="center", va="center", color="#94A3B8",
                    fontsize=11, transform=ax.transAxes, multialignment="center")
            ax.tick_params(colors="#94A3B8")
            return

        labels = ["Overdue"]
        for i in range(1, WEEKS_AHEAD + 1):
            monday = week_start + timedelta(weeks=i - 1)
            labels.append(monday.strftime("%-d %b"))

        bar_colors = ["#EF4444"] + ["#3B82F6"] * WEEKS_AHEAD

        x_pos = list(range(WEEKS_AHEAD + 1))
        bars = ax.bar(x_pos, counts, color=bar_colors, edgecolor="#0F172A",
                      linewidth=0.8, width=0.6)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, color="#F8FAFC", fontsize=8, rotation=35, ha="right")
        ax.set_ylabel("Items", color="#94A3B8", fontsize=9)
        ax.yaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#334155")
        ax.tick_params(axis="x", colors="#94A3B8")
        ax.tick_params(axis="y", colors="#94A3B8", labelsize=8)

        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.05,
                    str(count), ha="center", va="bottom",
                    color="#F8FAFC", fontsize=9, fontweight="bold",
                )

    # ── Chart 3 ──────────────────────────────────────────────────────

    def _draw_age_heatmap(self, ax):
        """Scatter plot: X = days since creation, Y = status — spots stale items per column."""
        board = self._board
        today = date.today()

        # Collect (age_days, status_label, item_type) for every item
        TYPE_LABELS = {"Epic": "Epic", "Task": "Task", "ChildTask": "Sub-task"}
        TYPE_COLORS = {"Epic": "#F59E0B", "Task": "#3B82F6", "ChildTask": "#10B981"}

        status_labels = [s.label for s in board.statuses]
        status_index = {s.label: i for i, s in enumerate(board.statuses)}

        points = []  # (x, y, color, type_label)
        for item in board.all_items():
            status = board.get_status(item.status_id)
            if not status or not item.created_at:
                continue
            age = (today - item.created_at.date()).days
            type_name = type(item).__name__
            color = TYPE_COLORS.get(type_name, "#94A3B8")
            label = TYPE_LABELS.get(type_name, type_name)
            points.append((age, status_index[status.label], color, label))

        ax.set_facecolor("#1E293B")
        ax.set_title("Item Age by Status", color="#F8FAFC", fontsize=13, pad=14)

        if not points:
            ax.text(0.5, 0.5, "No items on board", ha="center", va="center",
                    color="#94A3B8", fontsize=11, transform=ax.transAxes)
            return

        # Jitter Y slightly so overlapping dots don't merge
        import random
        random.seed(42)
        for age, y_idx, color, label in points:
            jitter = random.uniform(-0.18, 0.18)
            ax.scatter(age, y_idx + jitter, color=color, s=48,
                       edgecolors="#0F172A", linewidths=0.6, alpha=0.85, zorder=3)

        # Legend
        for type_name, color in TYPE_COLORS.items():
            ax.scatter([], [], color=color, s=40, label=TYPE_LABELS[type_name],
                       edgecolors="#0F172A", linewidths=0.6)
        ax.legend(loc="upper left", fontsize=7, framealpha=0.15,
                  labelcolor="#F8FAFC", facecolor="#1E293B", edgecolor="#334155")

        ax.set_yticks(range(len(status_labels)))
        ax.set_yticklabels(status_labels, color="#F8FAFC", fontsize=8)
        ax.set_xlabel("Days since creation", color="#94A3B8", fontsize=9)
        ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))

        for spine in ("top", "right"):
            ax.spines[spine].set_visible(False)
        for spine in ("left", "bottom"):
            ax.spines[spine].set_color("#334155")
        ax.tick_params(axis="x", colors="#94A3B8", labelsize=8)
        ax.tick_params(axis="y", colors="#94A3B8")
        ax.grid(axis="x", color="#334155", linewidth=0.5, linestyle="--", alpha=0.5)
