import asyncio
import os
import cv2
import numpy as np
import math
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Настройки протокола "Холодной Синергии"
VURF = 1.618033
API_TOKEN = os.getenv('BOT_TOKEN', 'ТВОЙ_ТОКЕН')
MODEL_BIN = 'gideon_core.npy'
VIDEO_PATH = 'test_video.mp4'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def load_structure():
    if not os.path.exists(MODEL_BIN):
        return None
    # Загружаем бинарные координаты
    return np.load(MODEL_BIN)

@dp.message(Command("render_video"))
async def render(message: types.Message):
    coords = load_structure()
    if coords is None:
        return await message.answer("❌ Ядро GIDEON не найдено (нужен .npy файл)")

    status = await message.answer("🌀 Запуск S-Vision: Фаза когерентности SAI 1.0...")

    cap = cv2.VideoCapture(VIDEO_PATH)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    res = 1024
    out = cv2.VideoWriter('render.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (res, res))

    frame_idx = 0
    total_nodes = len(coords)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break

        # Подготовка цветов (инстансинг под размер модели)
        frame_resized = cv2.resize(frame, (res, res))
        colors = frame_resized.reshape(-1, 3)
        if len(colors) != total_nodes:
            colors = np.resize(colors, (total_nodes, 3))

        canvas = np.zeros((res, res, 3), dtype=np.uint8)

        # --- 3D ПРОЕКЦИЯ GIDEON (S-GPU Logic) ---
        angle = frame_idx * 0.05 / VURF
        s, c = math.sin(angle), math.cos(angle)
        
        # Вращение вокруг оси Y (имитация объема)
        x = coords[:, 0]
        y = coords[:, 1]
        z = coords[:, 2]

        # Математика поворота
        x_rot = x * c - z * s
        z_rot = x * s + z * c
        
        # Проекция на 2D экран с учетом глубины Z (Перспектива)
        # Чем дальше Z, тем ближе точки к центру
        depth_factor = (z_rot - z_rot.min()) / (z_rot.max() - z_rot.min() + 1)
        fov = 500 # Поле зрения
        
        screen_x = (x_rot * fov / (z_rot + 1000) + res/2).astype(int)
        screen_y = (y * fov / (z_rot + 1000) + res/2).astype(int)

        # Ограничение границ
        mask = (screen_x >= 0) & (screen_x < res) & (screen_y >= 0) & (screen_y < res)
        canvas[screen_y[mask], screen_x[mask]] = colors[mask]

        out.write(canvas)
        frame_idx += 1

    cap.release()
    out.release()
    await bot.send_video(message.chat.id, types.FSInputFile('render.mp4'), caption="✅ SAI 1.0: Когерентность подтверждена")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())