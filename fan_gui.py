#!/usr/bin/env python3

import pathlib
import sys
import tkinter as tk
from functools import partial
from tkinter import messagebox

BASE_DIR = pathlib.Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import controller
import fan_profile

CPU_LABELS = [
    "CPU Step 1",
    "CPU Step 2",
    "CPU Step 3",
    "CPU Step 4",
    "CPU Step 5",
    "CPU Step 6",
    "CPU Step 7",
]

GPU_LABELS = [
    "GPU Step 1",
    "GPU Step 2",
    "GPU Step 3",
    "GPU Step 4",
    "GPU Step 5",
    "GPU Step 6",
    "GPU Step 7",
]

# Temperature thresholds shown below ogni slider (°C)
TEMP_POINTS = [40, 50, 60, 70, 80, 90, 100]

SCALE_LENGTH = 220
STAT_REFRESH_MS = 2000


class FanCurveApp:
    def __init__(self, root):
        self.root = root
        root.title("GP66 Fan Curve")
        root.resizable(False, False)

        self.flag_var = tk.IntVar()
        self.cpu_vars = [tk.IntVar() for _ in range(7)]
        self.gpu_vars = [tk.IntVar() for _ in range(7)]
        self.cpu_display = [tk.StringVar() for _ in range(7)]
        self.gpu_display = [tk.StringVar() for _ in range(7)]
        self.cpu_temps = TEMP_POINTS.copy()
        self.gpu_temps = TEMP_POINTS.copy()
        self.stats_vars = {
            "cpu": tk.StringVar(value="CPU: -- °C / -- RPM"),
            "gpu": tk.StringVar(value="GPU: -- °C / -- RPM"),
        }

        self._build_ui()
        self._load_profile()
        self._refresh_stats()

    def _build_ui(self):
        info = (
            "Ogni slider imposta la percentuale PWM quando la temperatura supera la soglia indicata."
            " Le soglie sono fisse (°C) sotto gli slider; aumenta il valore per spingere le ventole."
        )
        tk.Label(self.root, text=info, wraplength=540, justify="left").grid(
            row=0, column=0, columnspan=3, pady=(10, 10), padx=12, sticky="w"
        )

        flag_frame = tk.Frame(self.root)
        flag_frame.grid(row=1, column=0, columnspan=3, sticky="w", padx=12)
        tk.Label(flag_frame, text="Flag iniziale (0-255, lascia 13 se in dubbio):").pack(
            side="left"
        )
        tk.Spinbox(flag_frame, from_=0, to=255, textvariable=self.flag_var, width=5).pack(
            side="left", padx=(6, 0)
        )

        cpu_frame = tk.LabelFrame(self.root, text="Ventola CPU")
        cpu_frame.grid(row=2, column=0, padx=(12, 6), pady=10)
        self._build_slider_group(
            cpu_frame,
            CPU_LABELS,
            self.cpu_vars,
            self.cpu_display,
            self.cpu_temps,
        )

        gpu_frame = tk.LabelFrame(self.root, text="Ventola GPU")
        gpu_frame.grid(row=2, column=1, padx=(6, 6), pady=10)
        self._build_slider_group(
            gpu_frame,
            GPU_LABELS,
            self.gpu_vars,
            self.gpu_display,
            self.gpu_temps,
        )

        stats_frame = tk.LabelFrame(self.root, text="Sensori")
        stats_frame.grid(row=2, column=2, padx=(6, 12), pady=10, sticky="n")
        tk.Label(stats_frame, textvariable=self.stats_vars["cpu"], anchor="w", width=26).pack(
            padx=6, pady=(10, 6)
        )
        tk.Label(stats_frame, textvariable=self.stats_vars["gpu"], anchor="w", width=26).pack(
            padx=6, pady=(0, 10)
        )

        btn_frame = tk.Frame(self.root)
        btn_frame.grid(row=3, column=0, columnspan=3, pady=(0, 12))

        tk.Button(btn_frame, text="Applica e salva", command=self._save_and_apply).pack(
            side="left", padx=6
        )
        tk.Button(btn_frame, text="Solo salva", command=self._save_only).pack(
            side="left", padx=6
        )
        tk.Button(btn_frame, text="Ripristina default", command=self._reset_defaults).pack(
            side="left", padx=6
        )

        warn = "Serve eseguire come root per scrivere la configurazione e l'EC."
        tk.Label(self.root, text=warn, fg="red").grid(
            row=4, column=0, columnspan=3, pady=(0, 12)
        )

    def _build_slider_group(self, parent, labels, variables, displays, temps):
        for idx, (label, var, display_var, temp) in enumerate(
            zip(labels, variables, displays, temps)
        ):
            col_frame = tk.Frame(parent)
            col_frame.grid(row=0, column=idx, padx=4, pady=6)
            tk.Label(col_frame, text=label).pack(pady=(0, 4))
            scale = tk.Scale(
                col_frame,
                from_=255,
                to=0,
                orient="vertical",
                length=SCALE_LENGTH,
                resolution=1,
                variable=var,
            )
            scale.pack()
            callback = partial(self._update_slider_text, var, display_var, temp)
            var.trace_add("write", callback)
            callback()
            tk.Label(col_frame, textvariable=display_var).pack(pady=(4, 0))

    @staticmethod
    def _update_slider_text(var, text_var, temp, *_args):
        text_var.set(f"≥ {temp} °C → {var.get()}%")

    def _load_profile(self):
        try:
            profile = fan_profile.load_profile()
        except Exception as exc:
            messagebox.showerror("Errore", f"Impossibile caricare la configurazione: {exc}")
            profile = fan_profile.DEFAULT_PROFILE

        self.flag_var.set(profile["flag"])
        for var, display, temp, value in zip(
            self.cpu_vars, self.cpu_display, self.cpu_temps, profile["cpu"]
        ):
            var.set(value)
            self._update_slider_text(var, display, temp)
        for var, display, temp, value in zip(
            self.gpu_vars, self.gpu_display, self.gpu_temps, profile["gpu"]
        ):
            var.set(value)
            self._update_slider_text(var, display, temp)

    def _collect_profile(self):
        return {
            "flag": self.flag_var.get(),
            "cpu": [var.get() for var in self.cpu_vars],
            "gpu": [var.get() for var in self.gpu_vars],
        }

    def _save_only(self):
        try:
            fan_profile.save_profile(self._collect_profile())
        except Exception as exc:
            messagebox.showerror("Errore", f"Salvataggio fallito: {exc}")
            return
        messagebox.showinfo("OK", "Configurazione salvata.")

    def _save_and_apply(self):
        try:
            profile = self._collect_profile()
            fan_profile.save_profile(profile)
            fan_profile.apply_profile(profile)
        except PermissionError as exc:
            messagebox.showerror("Permessi", f"Permesso negato: {exc}")
            return
        except Exception as exc:
            messagebox.showerror("Errore", f"Applicazione fallita: {exc}")
            return
        messagebox.showinfo("OK", "Configurazione applicata e salvata.")

    def _reset_defaults(self):
        self.flag_var.set(fan_profile.DEFAULT_PROFILE["flag"])
        for var, display, temp, value in zip(
            self.cpu_vars, self.cpu_display, self.cpu_temps, fan_profile.DEFAULT_PROFILE["cpu"]
        ):
            var.set(value)
            self._update_slider_text(var, display, temp)
        for var, display, temp, value in zip(
            self.gpu_vars, self.gpu_display, self.gpu_temps, fan_profile.DEFAULT_PROFILE["gpu"]
        ):
            var.set(value)
            self._update_slider_text(var, display, temp)

    def _refresh_stats(self):
        try:
            stats = controller.get_stats()
        except Exception:
            stats = {
                "CPU_TEMP": 0,
                "GPU_TEMP": 0,
                "CPU_RPM": 0,
                "GPU_RPM": 0,
            }
        cpu_temp = stats.get("CPU_TEMP", 0)
        gpu_temp = stats.get("GPU_TEMP", 0)
        cpu_rpm = stats.get("CPU_RPM", 0) or 0
        gpu_rpm = stats.get("GPU_RPM", 0) or 0
        self.stats_vars["cpu"].set(f"CPU: {cpu_temp} °C / {cpu_rpm} RPM")
        self.stats_vars["gpu"].set(f"GPU: {gpu_temp} °C / {gpu_rpm} RPM")
        self.root.after(STAT_REFRESH_MS, self._refresh_stats)


def main():
    root = tk.Tk()
    app = FanCurveApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
