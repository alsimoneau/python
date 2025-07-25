import random

import matplotlib.animation as animation
import matplotlib.pyplot as plt
import numpy as np


class SnakeGame:
    HIGH_SCORE_FILE = "highscore.txt"

    def __init__(self, grid_size=20):
        self.grid_size = grid_size
        self.fig = plt.figure(figsize=(7, 5))
        self.game_state = {}
        self.anim = None
        self.high_score = self.load_high_score()
        self.setup()

    def setup(self):
        self.game_state.clear()
        self.game_state["snake"] = [(10, 10)]
        self.game_state["apple"] = self.random_apple()
        self.game_state.update(
            {
                "direction": None,
                "input_queue": [],
                "game_over": False,
                "paused": False,
                "score": 0,
                "head_visits": np.zeros((self.grid_size, self.grid_size), dtype=int),
                "move_counts": [],
                "current_moves": 0,
                "shrinking_after_gameover": 0,
                "input_locked": False,
            }
        )

        self.fig.clf()
        self.fig.suptitle(
            f"Score: {self.game_state['score']} | High Score: {self.high_score}",
            fontsize=14,
            color="blue",
        )
        self.subtitle = self.fig.text(
            0.5, 0.89, "", ha="center", fontsize=12, color="gray"
        )

        gs = self.fig.add_gridspec(1, 3, width_ratios=[1, 6, 1])
        self.ax = self.fig.add_subplot(gs[1])
        self.bar_ax = self.fig.add_subplot(gs[2])

        self.ax.set_xlim(-0.5, self.grid_size - 0.5)
        self.ax.set_ylim(-0.5, self.grid_size - 0.5)
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_aspect("equal")

        self.bar_ax.set_xticks([])
        self.bar_ax.set_yticks([])
        for spine in self.bar_ax.spines.values():
            spine.set_visible(False)

        self.fig.canvas.mpl_connect("key_press_event", self.on_key)
        self.game_state["snake_plot"] = self.ax.scatter([], [], s=300)
        self.game_state["apple_plot"] = self.ax.scatter([], [], c="red", s=300)

    def random_apple(self):
        while True:
            apple = (
                random.randint(0, self.grid_size - 1),
                random.randint(0, self.grid_size - 1),
            )
            if apple not in self.game_state["snake"]:
                return apple

    def on_key(self, event):
        if self.game_state.get("input_locked", False):
            return

        if event.key == "escape":
            plt.close(self.fig)
            return

        direction_map = {
            "up": (0, 1),
            "down": (0, -1),
            "left": (-1, 0),
            "right": (1, 0),
        }

        if self.game_state["game_over"]:
            if event.key in direction_map or event.key == " ":
                self.setup()
                if event.key in direction_map:
                    self.game_state["direction"] = direction_map[event.key]
                return

        if event.key == " ":
            self.game_state["paused"] = not self.game_state["paused"]
            if self.game_state["paused"]:
                self.subtitle.set_text("Paused — Press Space to Resume")
            else:
                self.subtitle.set_text("")
            return

        new_dir = direction_map.get(event.key)
        if new_dir:
            self.game_state["input_queue"].append(new_dir)

    def compute_snake_colors(self, length):
        max_len = max(length, 30)
        return [(0, (1 - i / (max_len - 1)), 0) for i in reversed(range(length))]

    def is_valid_direction_change(self, curr_dir, new_dir):
        return (
            curr_dir is None
            or curr_dir[0] + new_dir[0] != 0
            and curr_dir[1] + new_dir[1] != 0
        )

    def is_collision(self, pos):
        x, y = pos
        return (
            pos in self.game_state["snake"]
            or not (0 <= x < self.grid_size)
            or not (0 <= y < self.grid_size)
        )

    def eat_apple(self):
        self.game_state["score"] += 1
        if self.game_state["score"] > self.high_score:
            self.high_score = self.game_state["score"]
        self.fig.suptitle(
            f"Score: {self.game_state['score']} | High Score: {self.high_score}",
            fontsize=14,
            color="blue",
        )
        self.game_state["apple"] = self.random_apple()
        self.game_state["move_counts"].append(self.game_state["current_moves"])
        self.game_state["current_moves"] = 0

    def draw_bar_plot(self, ax):
        num_apples = max(len(self.game_state["move_counts"]), 20)
        counts = self.game_state["move_counts"] + [0] * (
            num_apples - len(self.game_state["move_counts"])
        )
        ax.barh(range(1, num_apples + 1), counts[:num_apples], color="green")
        ax.invert_yaxis()
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)

    def update_bar_plot(self):
        self.bar_ax.clear()
        self.draw_bar_plot(self.bar_ax)

    def handle_game_over(self):
        self.game_state["game_over"] = True
        self.game_state["shrinking_after_gameover"] = 5
        self.game_state["input_queue"].clear()
        self.game_state["input_locked"] = True

    def finalize_game_over_screen(self):
        self.game_state["input_locked"] = False
        self.fig.suptitle(
            f"Game Over. Score: {self.game_state['score']} | High Score: {self.high_score}",
            fontsize=14,
            color="red",
        )
        self.ax.clear()
        self.ax.set_title("Snake Head Movement Heatmap", fontsize=12)
        self.ax.imshow(
            self.game_state["head_visits"],
            cmap="hot",
            interpolation="nearest",
            origin="lower",
        )
        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.update_bar_plot()

    def load_high_score(self):
        try:
            with open(self.HIGH_SCORE_FILE, "r") as f:
                return int(f.read().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def save_high_score(self):
        with open(self.HIGH_SCORE_FILE, "w") as f:
            f.write(str(self.high_score))

    def update(self, frame):
        if self.game_state["paused"]:
            return

        if self.game_state["shrinking_after_gameover"] > 0:
            step = self.game_state["shrinking_after_gameover"] - 1
            scale = step / 5
            new_size = 300 * scale

            self.fig.suptitle(
                f"Game Over. Score: {self.game_state['score']} | High Score: {self.high_score}",
                fontsize=14,
                color="red",
            )

            self.game_state["snake_plot"].set_offsets(
                np.array(self.game_state["snake"])
            )
            self.game_state["snake_plot"].set_sizes(
                [new_size] * len(self.game_state["snake"])
            )
            self.game_state["snake_plot"].set_color(
                self.compute_snake_colors(len(self.game_state["snake"]))
            )

            self.game_state["shrinking_after_gameover"] -= 1

            if self.game_state["shrinking_after_gameover"] == 0:
                self.finalize_game_over_screen()
            return

        if self.game_state["game_over"]:
            return

        while self.game_state["input_queue"]:
            next_dir = self.game_state["input_queue"].pop(0)
            if self.is_valid_direction_change(self.game_state["direction"], next_dir):
                self.game_state["direction"] = next_dir
                break

        if self.game_state["direction"] is None:
            return

        head_x, head_y = self.game_state["snake"][-1]
        dx, dy = self.game_state["direction"]
        new_head = (head_x + dx, head_y + dy)

        self.game_state["current_moves"] += 1

        if 0 <= new_head[0] < self.grid_size and 0 <= new_head[1] < self.grid_size:
            self.game_state["head_visits"][new_head[1], new_head[0]] += 1

        if self.is_collision(new_head):
            self.handle_game_over()
            return

        self.game_state["snake"].append(new_head)

        if new_head == self.game_state["apple"]:
            self.eat_apple()
        else:
            self.game_state["snake"].pop(0)

        self.game_state["snake_plot"].set_offsets(np.array(self.game_state["snake"]))
        self.game_state["snake_plot"].set_color(
            self.compute_snake_colors(len(self.game_state["snake"]))
        )
        self.game_state["snake_plot"].set_sizes([300] * len(self.game_state["snake"]))
        self.game_state["apple_plot"].set_offsets([self.game_state["apple"]])

        self.update_bar_plot()

    def run(self):
        self.anim = animation.FuncAnimation(
            self.fig, self.update, interval=100, cache_frame_data=False
        )
        plt.show()
        self.save_high_score()


if __name__ == "__main__":
    SnakeGame().run()
