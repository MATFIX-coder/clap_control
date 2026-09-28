import pystray
from PIL import Image, ImageDraw
import tkinter as tk
import threading
import time
import ctypes

import sounddevice as sd
import numpy as np


# Настройки распознавания
BLOCK_SIZE = 1024
THRESHOLD = 0.25
COOLDOWN = 0.3
CLAPS_NEEDED = 3
MAX_INTERVAL = 1.0

# Показывает, должна ли программа сейчас слушать микрофон
running = False


def listen_for_claps():
    """
    Эта функция постоянно слушает микрофон.
    Она будет работать отдельно от интерфейса.
    """

    global running

    last_clap_time = 0
    clap_count = 0

    with sd.InputStream(
        channels=1,
        blocksize=BLOCK_SIZE,
        dtype="float32"
    ) as stream:

        while running:

            # Получаем небольшой кусок звука
            audio, overflowed = stream.read(BLOCK_SIZE)

            # Находим максимальную громкость
            volume = np.max(np.abs(audio))

            current_time = time.time()

            # Проверяем, достаточно ли громкий звук
            if volume > THRESHOLD:

                # Не считаем один хлопок несколько раз
                if current_time - last_clap_time > COOLDOWN:

                    # Если слишком долго не было следующего хлопка —
                    # начинаем последовательность заново
                    if current_time - last_clap_time > MAX_INTERVAL:
                        clap_count = 0

                    clap_count += 1
                    last_clap_time = current_time


                    # Получили три хлопка
                    if clap_count == CLAPS_NEEDED:


                        # Включаем погасший экран
                        ctypes.windll.kernel32.SetThreadExecutionState(
                            0x00000002
                        )

                        clap_count = 0


def start_listening():
    global running

    # Если уже работает — второй раз не запускаем
    if running:
        return

    running = True
    tray_icon.icon = create_tray_image("green")

    status_label.config(text="Listening")

    start_button.config(state="disabled")
    stop_button.config(state="normal")

    # Запускаем распознавание в отдельном потоке
    thread = threading.Thread(
        target=listen_for_claps,
        daemon=True
    )

    thread.start()

    root.withdraw()  # Полностью скрываем окно и убираем его с панели задач


def stop_listening():
    global running

    running = False
    tray_icon.icon = create_tray_image("red")

    status_label.config(text="Stopped")

    start_button.config(state="normal")
    stop_button.config(state="disabled")


def close_program():
    global running

    running = False

    tray_icon.stop()  # Убираем значок возле часов
    root.destroy()


# Создаём окно приложения
root = tk.Tk()

root.title("Clap Control")
root.geometry("300x180")
root.resizable(False, False)

title_label = tk.Label(
    root,
    text="Clap Control",
    font=("Arial", 18)
)
title_label.pack(pady=15)

status_label = tk.Label(
    root,
    text="Stopped",
    font=("Arial", 11)
)
status_label.pack(pady=5)

start_button = tk.Button(
    root,
    text="START",
    font=("Arial", 14),
    width=15,
    command=start_listening
)
start_button.pack(pady=5)

stop_button = tk.Button(
    root,
    text="STOP",
    font=("Arial", 10),
    width=15,
    command=stop_listening,
    state="disabled"
)
stop_button.pack()

# Что делать при нажатии крестика
root.protocol("WM_DELETE_WINDOW", close_program)

def create_tray_image(color):
    # Создаём прозрачную иконку 64x64
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Рисуем цветной круг
    draw.ellipse((10, 10, 54, 54), fill=color)

    return image


def show_window(icon=None, item=None):
    # pystray работает в другом потоке,
    # поэтому просим Tkinter открыть окно через root.after
    root.after(0, _show_window)


def _show_window():
    root.deiconify()
    root.lift()


def tray_start(icon=None, item=None):
    root.after(0, start_listening)


def tray_stop(icon=None, item=None):
    root.after(0, stop_listening)


def tray_exit(icon=None, item=None):
    root.after(0, close_program)


tray_icon = pystray.Icon(
    "ClapControl",
    create_tray_image("red"),
    "Clap Control",
    menu=pystray.Menu(
        pystray.MenuItem("Open", show_window),
        pystray.MenuItem("Start", tray_start),
        pystray.MenuItem("Stop", tray_stop),
        pystray.MenuItem("Exit", tray_exit),
    )
)

# Запускаем значок в трее отдельно от интерфейса
tray_icon.run_detached()

# Запускаем интерфейс
root.mainloop()