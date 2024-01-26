import pygame
import random
import os
import re
import math
import time
import struct
import json
import memprocfs
import pygame_gui


radar_x = 0 # смещение радара по оси x
radar_y = 0 # смещение радара по оси y
dragging = False # флаг, указывающий, перетаскивается ли радар мышью

def get_map_name():
    with open(os.path.join(f'map.txt'), 'r') as f:
        maptxt = 'de_mirage'
    return maptxt

def load_map_data(map_name):
    with open(os.path.join('static', f'{map_name}.txt'), 'r') as f:
        content = f.read()
        map_data = {}
        for key, value in re.findall(r'"([^"]+)"\s+"([^"]+)"', content):
            try:
                map_data[key] = float(value)
            except ValueError:
                map_data[key] = value
    return map_data
 
def handle_events():
    global radar_x, radar_y, dragging # объявите глобальные переменные
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        elif event.type == pygame.VIDEORESIZE:
            screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        elif event.type == pygame.MOUSEBUTTONDOWN: # если нажата кнопка мыши
            if event.button == 1: # если нажата левая кнопка мыши
                dragging = True # установите флаг перетаскивания в True
        elif event.type == pygame.MOUSEBUTTONUP: # если отпущена кнопка мыши
            if event.button == 1: # если отпущена левая кнопка мыши
                dragging = False # установите флаг перетаскивания в False
        elif event.type == pygame.MOUSEMOTION: # если мышь движется
            if dragging: # если перетаскивается радар
                # получите смещение мыши по осям x и y
                dx, dy = event.rel
                # прибавьте смещение к смещению радара
                radar_x += dx
                radar_y += dy
    return True
 
 
def rotate_point(center, point, angle):
    """
    Rotates a point around another center point.
    """
    angle_rad = math.radians(angle)
    temp_point = point[0] - center[0], center[1] - point[1]
    temp_point = (temp_point[0]*math.cos(angle_rad)-temp_point[1]*math.sin(angle_rad), temp_point[0]*math.sin(angle_rad)+temp_point[1]*math.cos(angle_rad))
    temp_point = temp_point[0] + center[0], center[1] - temp_point[1]
    return temp_point
 
def world_to_minimap(x, y, pos_x, pos_y, scale, map_image, screen, player_x, player_y, zoom_scale, rotation_angle):
    image_x = int((x + pos_x) * screen.get_width() / (map_image.get_width() * scale * zoom_scale))
    image_y = int((pos_y + y) * screen.get_height() / (map_image.get_height() * scale * zoom_scale))

    center_x, center_y = screen.get_width() // 2, screen.get_height() // 2
    image_x, image_y = image_x - center_x, image_y - center_y

    # Добавьте смещение радара к координатам изображения
    image_x += radar_x
    image_y += radar_y

    return int(center_x + image_x), int(center_y + image_y)
 
 
def rotate_image(image, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center = image.get_rect().center)
    return rotated_image, new_rect
 
 
def initialize_pygame(map_image):
    pygame.init()
    display_info = pygame.display.Info()
    screen_width, screen_height = 600, 600
    screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
    pygame.display.set_caption("Game Radar")
    clock = pygame.time.Clock()
    return screen, clock
 
 
def main():
    dwEntityList = 0x17CE6A0
    dwLocalPlayerPawn = 0x16D4F48
    m_iHealth = 0x32C
    m_vOldOrigin = 0x1224
    vmm = memprocfs.Vmm(['-device', 'fpga', '-disable-python', '-disable-symbols', '-disable-symbolserver', '-disable-yara', '-disable-yara-builtin', '-debug-pte-quality-threshold', '64'])
    cs2 = vmm.process('cs2.exe')
    client = cs2.module('client.dll')
    client_base = client.base
    print(f"[+] Client_base {client_base}")
    entList = struct.unpack("<Q", cs2.memory.read(client_base + dwEntityList, 8, memprocfs.FLAG_NOCACHE))[0]
    print(f"[+] Entitylist {entList}")
    player = struct.unpack("<Q", cs2.memory.read(client_base + dwLocalPlayerPawn, 8, memprocfs.FLAG_NOCACHE))[0]
    print(f"[+] Player {player}")

    entitys = []
    for entityId in range(1,700):
        EntityENTRY = struct.unpack("<Q", cs2.memory.read((entList + 0x8 * (entityId >> 9) + 0x10), 8, memprocfs.FLAG_NOCACHE))[0]
        try:
            entity = struct.unpack("<Q", cs2.memory.read(EntityENTRY + 120 * (entityId & 0x1FF), 8, memprocfs.FLAG_NOCACHE))[0]
            entityHp = struct.unpack("<I", cs2.memory.read(entity + m_iHealth, 4, memprocfs.FLAG_NOCACHE))[0]
            if int(entityHp) != 0:
                entitys.append(entityId)
            else:
                pass
        except:
            pass
 
    
    map_name = get_map_name()
    map_data = load_map_data(map_name)
    map_image = pygame.image.load(os.path.join('static', f'{map_name}_radar.png'))
 
    screen, clock = initialize_pygame(map_image)
    font = pygame.font.Font(None, 24)
    height_tolerance = 65
    zoom_scale = 2

    running = True
    while running:
        try:
 
            screen.fill((0, 0, 0))
 
            rotated_map_image, map_rect = pygame.transform.scale(map_image, screen.get_size()), map_image.get_rect()
            screen.blit(rotated_map_image, map_rect.topleft)
 
            for entityId in entitys:
                EntityENTRY = struct.unpack("<Q", cs2.memory.read((entList + 0x8 * (entityId >> 9) + 0x10), 8, memprocfs.FLAG_NOCACHE))[0]
                entity = struct.unpack("<Q", cs2.memory.read(EntityENTRY + 120 * (entityId & 0x1FF), 8, memprocfs.FLAG_NOCACHE))[0]
                entity_health = struct.unpack("<I", cs2.memory.read(entity + m_iHealth, 4, memprocfs.FLAG_NOCACHE))[0]
                entity_pos_x = struct.unpack("<f", cs2.memory.read(entity + m_vOldOrigin +0x4, 4, memprocfs.FLAG_NOCACHE))[0]
                entity_pos_y = struct.unpack("<f", cs2.memory.read(entity + m_vOldOrigin, 4, memprocfs.FLAG_NOCACHE))[0]
                player_view_angle_y = 1
                x, y = entity_pos_x, entity_pos_y
                pos_x, pos_y, scale = map_data['pos_x'], map_data['pos_y'], map_data['scale']
                image_x, image_y = world_to_minimap(x, y, pos_x, pos_y, scale, map_image, screen, entity_pos_x, entity_pos_y, zoom_scale, player_view_angle_y)
 
                if entity_health > 0:
                    pygame.draw.circle(screen, (255, 0, 0), (image_x, image_y), 5)
                    health_text = font.render(str(entity_health), True, (255, 255, 255))
                    screen.blit(health_text, (image_x + 10, image_y - 20))
 
 
            pygame.display.update()
            clock.tick(60)
        except KeyboardInterrupt:
            vmm.close()
            print("Stopped.")
            break
    pygame.quit()
 
if __name__ == "__main__":
    main()