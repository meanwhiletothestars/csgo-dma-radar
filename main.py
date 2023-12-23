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
        maptxt = f.read()
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
    image_x = int((x - pos_x) * screen.get_width() / (map_image.get_width() * scale * zoom_scale))
    image_y = int((pos_y - y) * screen.get_height() / (map_image.get_height() * scale * zoom_scale))

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
 
 
def read_memory(process, address, size):
    return struct.unpack(f"<{size}B", process.memory.read(address, size))
 
 
def read_float_memory(process, address):
    return struct.unpack("<f", process.memory.read(address, 4))[0]
 
 
def read_int_memory(process, address):
    return struct.unpack("<I", process.memory.read(address, 4))[0]
 
 
def main():
    vmm = memprocfs.Vmm(['-device', 'fpga'])
    process_csgo = vmm.process('csgo.exe')
    module_client = process_csgo.module('client.dll')
    client_dll_base = module_client.base
 
    with open('csgo.min.json', 'r') as f:
        data = json.load(f)
    signatures = {key: hex(value) for key, value in data['signatures'].items()}
    netvars = {key: hex(value) for key, value in data['netvars'].items()}
 
    dwLocalPlayer = int(signatures['dwLocalPlayer'], 16)
    m_vecOrigin = int(netvars['m_vecOrigin'], 16)
    m_angEyeAnglesX = int(netvars['m_angEyeAnglesX'], 16)
    m_angEyeAnglesY = int(netvars['m_angEyeAnglesY'], 16)
    dwEntityList = int(signatures['dwEntityList'], 16)
    m_iTeamNum = int(netvars['m_iTeamNum'], 16)
    m_iHealth = int(netvars['m_iHealth'], 16)
    m_bIsDefusing = int(netvars['m_bIsDefusing'], 16)
    
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
            local_player_address = read_int_memory(process_csgo, client_dll_base + dwLocalPlayer)
            local_player = local_player_address
 
            player_pos_address = local_player + m_vecOrigin
            player_pos_x = read_float_memory(process_csgo, player_pos_address)
            print(player_pos_x)
            player_pos_y = read_float_memory(process_csgo, player_pos_address + 4)
            print(player_pos_y)
            player_pos_z = read_float_memory(process_csgo, player_pos_address + 8)
            print(player_pos_z)
            player_view_angle_x = read_float_memory(process_csgo, local_player + m_angEyeAnglesX)
            player_view_angle_y = read_float_memory(process_csgo, local_player + m_angEyeAnglesY)
 
            local_player_health_address = local_player + m_iHealth
            local_player_health = read_int_memory(process_csgo, local_player_health_address)
 
            running = handle_events()
 
            screen.fill((0, 0, 0))
 
            x, y, z = player_pos_x, player_pos_y, player_pos_z
            view_angle_x = player_view_angle_x
            view_angle_y = player_view_angle_y
 
            rotated_map_image, map_rect = pygame.transform.scale(map_image, screen.get_size()), map_image.get_rect()
            screen.blit(rotated_map_image, map_rect.topleft)
 
            pos_x, pos_y, scale = map_data['pos_x'], map_data['pos_y'], map_data['scale']
            image_x, image_y = world_to_minimap(x, y, pos_x, pos_y, scale, map_image, screen, player_pos_x, player_pos_y, zoom_scale, player_view_angle_y)
 
            local_player_team_address = local_player + m_iTeamNum
            local_player_team = read_int_memory(process_csgo, local_player_team_address)
 
            max_clients = 10  # You may need to adjust this value
            for i in range(max_clients):
                entity_address = read_int_memory(process_csgo, client_dll_base + dwEntityList + i * 0x10)
                entity = entity_address
                if not entity:
                    continue
 
                entity_team_address = entity + m_iTeamNum
                entity_team = read_int_memory(process_csgo, entity_team_address)
 
                entity_pos_address = entity + m_vecOrigin
                entity_pos_x = read_float_memory(process_csgo, entity_pos_address)
                entity_pos_y = read_float_memory(process_csgo, entity_pos_address + 4)
                entity_pos_z = read_float_memory(process_csgo, entity_pos_address + 8)
 
                entity_health_address = entity + m_iHealth
                entity_health = read_int_memory(process_csgo, entity_health_address)
 
                x, y, z = entity_pos_x, entity_pos_y, entity_pos_z
                image_x, image_y = world_to_minimap(x, y, pos_x, pos_y, scale, map_image, screen, player_pos_x, player_pos_y, zoom_scale, player_view_angle_y)
 
                if entity == local_player and local_player_health > 0:
                    pygame.draw.circle(screen, (0, 0, 255), (image_x, image_y), 5)
                elif entity_team != local_player_team and entity_health > 0:
                    pygame.draw.circle(screen, (255, 0, 0), (image_x, image_y), 5)
                    health_text = font.render(str(entity_health), True, (255, 255, 255))
                    screen.blit(health_text, (image_x + 10, image_y - 20))
 
                entity_view_angle_x = read_float_memory(process_csgo, entity + m_angEyeAnglesX)
                entity_view_angle_y = read_float_memory(process_csgo, entity + m_angEyeAnglesY)
 
                arrow_length = 15
                arrow_end_x = image_x + arrow_length * math.cos(math.radians(entity_view_angle_y))
                arrow_end_y = image_y - arrow_length * math.sin(math.radians(entity_view_angle_y))
                if entity == local_player and local_player_health > 0:
                    pygame.draw.line(screen, (0, 0, 255), (image_x, image_y), (arrow_end_x, arrow_end_y), 2)
                elif entity_team != local_player_team and entity_health > 0:
                    pygame.draw.line(screen, (255, 0, 0), (image_x, image_y), (arrow_end_x, arrow_end_y), 2)
 
                entity_is_defusing_address = entity + m_bIsDefusing
                entity_is_defusing = read_int_memory(process_csgo, entity_is_defusing_address)
 
                if entity_is_defusing:
                    cross_size = 10
                    pygame.draw.line(screen, (0, 255, 0), (image_x - cross_size, image_y - cross_size),
                                     (image_x + cross_size, image_y + cross_size), 2)
                    pygame.draw.line(screen, (0, 255, 0), (image_x + cross_size, image_y - cross_size),
                                     (image_x - cross_size, image_y + cross_size), 2)
 
                if entity_health > 0 and entity != local_player and entity_team != local_player_team:
                    if entity_pos_z > player_pos_z + height_tolerance:
                        arrow = pygame.Surface((7, 7), pygame.SRCALPHA)
                        pygame.draw.polygon(arrow, (255, 255, 0), [(3, 0), (0, 7), (6, 7)])
                        screen.blit(arrow, (image_x - 4, image_y - 15))
                    elif entity_pos_z < player_pos_z - height_tolerance:
                        arrow = pygame.Surface((7, 7), pygame.SRCALPHA)
                        pygame.draw.polygon(arrow, (255, 255, 0), [(0, 0), (6, 0), (3, 7)])
                        screen.blit(arrow, (image_x - 4, image_y + 8))
 
 
 
 
            pygame.display.update()
            clock.tick(60)
        except KeyboardInterrupt:
            vmm.close()
            print("Stopped.")
            break
    pygame.quit()
 
if __name__ == "__main__":
    main()