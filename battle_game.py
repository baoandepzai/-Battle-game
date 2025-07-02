import pygame
import time
import json
import os
import sys
import random

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RPG Đơn Giản")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 0, 200)
YELLOW = (200, 200, 0)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY = (100, 100, 100)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
BROWN = (139, 69, 19)

HIT_FLASH_COLOR = (255, 100, 100)
ACTION_FLASH_COLOR = (100, 255, 100)
FLASH_DURATION = 150

try:
    FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Arial.ttf")
    if not os.path.exists(FONT_PATH):
        FONT_PATH = "/sdcard/Documents/Arial.ttf"
        if not os.path.exists(FONT_PATH):
            FONT_PATH = os.path.expanduser("~/Documents/Arial.ttf")
    
    FONT_LARGE = pygame.font.Font(FONT_PATH, 74)
    FONT_MEDIUM = pygame.font.Font(FONT_PATH, 30)
    FONT_SMALL = pygame.font.Font(FONT_PATH, 25)
    FONT_TINY = pygame.font.Font(FONT_PATH, 20)
except pygame.error:
    print(f"Lỗi: Không tìm thấy font. Đảm bảo file font 'Arial.ttf' nằm cùng thư mục script hoặc trong /sdcard/Documents/.")
    print("Sử dụng font mặc định của Pygame (có thể không hỗ trợ tiếng Việt đầy đủ).")
    FONT_LARGE = pygame.font.Font(None, 74)
    FONT_MEDIUM = pygame.font.Font(None, 40)
    FONT_SMALL = pygame.font.Font(None, 25)
    FONT_TINY = pygame.font.Font(None, 20)

MESSAGE_DURATION = 3000 
END_SCREEN_DURATION = 3000
SAVE_FILE_NAME = "rpg_save_data.json"

current_character_index = 0 
chosen_boss_index = -1

class Item:
    def __init__(self, name, item_type, stats_bonus=None, heal=0, manaCost=0):
        self.name = name
        self.item_type = item_type
        self.stats_bonus = stats_bonus if stats_bonus else {}
        self.heal = heal
        self.manaCost = manaCost

    def to_dict(self):
        return {
            "name": self.name,
            "item_type": self.item_type,
            "stats_bonus": self.stats_bonus,
            "heal": self.heal,
            "manaCost": self.manaCost
        }

    @staticmethod
    def from_dict(data):
        return Item(data["name"], data["item_type"], data["stats_bonus"], data["heal"], data["manaCost"])

class Character:
    def __init__(self, name, hp, atk, mana, skill_name, skillDmg, skillMana, skillCd):
        self.name = name
        self.base_maxHp = hp
        self.base_attack = atk
        self.base_maxMana = mana
        self.hp = hp
        self.mana = mana
        self.skill = {
            "name": skill_name,
            "power": skillDmg,
            "mana_cost": skillMana,
            "cooldown_turns": skillCd,
            "current_cooldown": 0
        }
        self.inventory = []
        self.equipment = {"weapon": None, "armor": None}
        self.last_hit_time = 0
        self.last_action_time = 0

    @property
    def level(self):
        if GLOBAL_PLAYER_PROFILE:
            return GLOBAL_PLAYER_PROFILE.total_level
        return 1

    @property
    def maxHp(self):
        bonus = sum(item.stats_bonus.get('hp', 0) for item in self.equipment.values() if item)
        return self.base_maxHp + (self.level - 1) * 10 + bonus

    @property
    def attack(self):
        bonus = sum(item.stats_bonus.get('atk', 0) for item in self.equipment.values() if item)
        return self.base_attack + (self.level - 1) * 2 + bonus

    @property
    def maxMana(self):
        bonus = sum(item.stats_bonus.get('mana', 0) for item in self.equipment.values() if item)
        return self.base_maxMana + (self.level - 1) * 5 + bonus
    
    @property
    def skill_power_calc(self):
        return self.skill["power"] + (self.level - 1) * 3

    @property
    def skill_mana_cost_calc(self):
        return self.skill["mana_cost"] + (self.level - 1) * 2

    def reset_stats(self):
        self.hp = self.maxHp
        self.mana = self.maxMana
        self.skill["current_cooldown"] = 0

    def add_item(self, item):
        self.inventory.append(item)

    def equip_item(self, item_index):
        if 0 <= item_index < len(self.inventory):
            item = self.inventory[item_index]
            if item.item_type in self.equipment:
                if self.equipment[item.item_type]:
                    self.inventory.append(self.equipment[item.item_type])
                self.equipment[item.item_type] = item
                self.inventory.pop(item_index)
                print(f"{self.name} đã trang bị {item.name}.")
                self.hp = min(self.hp, self.maxHp)
                self.mana = min(self.mana, self.maxMana)
                return True
        return False

    def unequip_item(self, item_type):
        if item_type in self.equipment and self.equipment[item_type]:
            self.inventory.append(self.equipment[item_type])
            print(f"{self.name} đã bỏ trang bị {self.equipment[item_type].name}.")
            self.equipment[item_type] = None
            self.hp = min(self.hp, self.maxHp) 
            self.mana = min(self.mana, self.maxMana)
            return True
        return False

    def use_consumable(self, item_index):
        if 0 <= item_index < len(self.inventory):
            item = self.inventory[item_index]
            if item.item_type == 'consumable':
                if item.manaCost < 0:
                    self.mana = min(self.mana - item.manaCost, self.maxMana)
                    self.inventory.pop(item_index)
                    print(f"{self.name} đã sử dụng {item.name}, hồi {-item.manaCost} Mana.")
                    return True
                elif self.mana >= item.manaCost:
                    self.hp = min(self.hp + item.heal, self.maxHp)
                    self.mana -= item.manaCost
                    self.inventory.pop(item_index)
                    print(f"{self.name} đã sử dụng {item.name}, hồi {item.heal} HP.")
                    return True
                else:
                    print(f"Không đủ mana để sử dụng {item.name}.")
        return False

    def to_dict(self):
        return {
            "name": self.name,
            "base_maxHp": self.base_maxHp,
            "base_attack": self.base_attack,
            "base_maxMana": self.base_maxMana,
            "hp": self.hp,
            "mana": self.mana,
            "skill": self.skill,
            "inventory": [item.to_dict() for item in self.inventory],
            "equipment": {k: v.to_dict() if v else None for k, v in self.equipment.items()}
        }

    @staticmethod
    def from_dict(data):
        char = Character(
            data["name"],
            data["base_maxHp"],
            data["base_attack"],
            data["base_maxMana"],
            data["skill"]["name"],
            data["skill"]["power"],
            data["skill"]["mana_cost"],
            data["skill"]["cooldown_turns"]
        )
        char.hp = data["hp"]
        char.mana = data["mana"]
        char.skill = data["skill"]
        char.inventory = [Item.from_dict(item_data) for item_data in data["inventory"]]
        char.equipment = {k: Item.from_dict(v) if v else None for k, v in data["equipment"].items()}
        return char

class PlayerProfile:
    def __init__(self):
        self.total_level = 1
        self.total_experience = 0
        self.exp_to_next_total_level = 100
        self.all_characters_data = {} 
        self.unlocked_character_names = set()

        for base_char in CHARACTER_DATA_BASE:
            self.all_characters_data[base_char.name] = base_char.to_dict()
        
        self.unlocked_character_names.add("conor")

    def add_exp(self, exp_gained):
        self.total_experience += exp_gained
        while self.total_experience >= self.exp_to_next_total_level:
            self.level_up()

    def level_up(self):
        self.total_level += 1
        self.total_experience -= self.exp_to_next_total_level
        self.exp_to_next_total_level = int(self.exp_to_next_total_level * 1.5)
        print(f"Tổng cấp độ người chơi đã lên cấp {self.total_level}!")
        self.check_unlocks()

    def check_unlocks(self):
        for char_name, level_req in CHARACTER_UNLOCK_LEVELS.items():
            if self.total_level >= level_req and char_name not in self.unlocked_character_names:
                self.unlocked_character_names.add(char_name)
                print(f"Nhân vật {char_name} đã được mở khóa!")

    def get_character_instance(self, character_name):
        char_data = self.all_characters_data.get(character_name)
        if char_data:
            return Character.from_dict(char_data)
        return None

    def update_character_data(self, character_instance):
        self.all_characters_data[character_instance.name] = character_instance.to_dict()

    def to_dict(self):
        return {
            "total_level": self.total_level,
            "total_experience": self.total_experience,
            "exp_to_next_total_level": self.exp_to_next_total_level,
            "unlocked_character_names": list(self.unlocked_character_names),
            "all_characters_data": self.all_characters_data
        }

    @staticmethod
    def from_dict(data):
        profile = PlayerProfile()
        profile.total_level = data["total_level"]
        profile.total_experience = data["total_experience"]
        profile.exp_to_next_total_level = data["exp_to_next_total_level"]
        profile.unlocked_character_names = set(data["unlocked_character_names"])
        profile.all_characters_data = data["all_characters_data"]
        profile.check_unlocks() 
        return profile

CHARACTER_DATA_BASE = [
    Character("conor", 150, 25, 200, "Slash", 45, 25, 3),
    Character("savior", 200, 20, 200, "Roar", 40, 20, 2),
    Character("justice", 125, 30, 250, "Fireball", 60, 30, 4),
    Character("ninja", 100, 35, 180, "Shuriken Toss", 50, 20, 2),
    Character("wizard", 110, 20, 300, "Blizzard", 70, 40, 5)
]

CHARACTER_UNLOCK_LEVELS = {
    "conor": 1, 
    "savior": 3,
    "justice": 5,
    "ninja": 7,
    "wizard": 10
}

GLOBAL_PLAYER_PROFILE = PlayerProfile()
current_character_instance = None

class Enemy:
    def __init__(self, name, hp, atk, exp_reward):
        self.name = name
        self.maxHp = hp
        self.hp = hp
        self.attack = atk
        self.exp_reward = exp_reward
        self.last_hit_time = 0

    def take_damage(self, damage):
        self.hp -= damage
        if self.hp < 0:
            self.hp = 0

    def heal(self, amount):
        self.hp = min(self.hp + amount, self.maxHp)

    def get_action(self, player_current_hp):
        if self.name == "King Slime" and self.hp < self.maxHp * 0.4:
            return "heal"
        elif player_current_hp < GLOBAL_PLAYER_PROFILE.get_character_instance(current_character_instance.name).maxHp * 0.35: 
            return "critical_attack"
        else:
            return "normal_attack"

BOSS_DATA = [
    Enemy("Goblin King", 300, 20, 50),
    Enemy("Orc Warlord", 450, 30, 100),
    Enemy("King Slime", 600, 25, 150),
    Enemy("Dragon Hatchling", 700, 35, 200),
    Enemy("Ancient Golem", 900, 40, 250)
]

ALL_ITEMS = [
    Item("Kiếm Sắt", "weapon", {"atk": 10}),
    Item("Áo Giáp Da", "armor", {"hp": 20}),
    Item("Bình Máu Nhỏ", "consumable", heal=50, manaCost=5),
    Item("Cung Gỗ", "weapon", {"atk": 8}),
    Item("Khiên Gỗ", "armor", {"hp": 15}),
    Item("Bình Mana Nhỏ", "consumable", heal=0, manaCost=-50)
]

def draw_button(screen_surface, text, x, y, width, height, inactive_color, active_color, action=None, font=None):
    if font is None:
        font = FONT_MEDIUM

    mouse_pos = pygame.mouse.get_pos()
    mouse_click = pygame.mouse.get_pressed()

    button_rect = pygame.Rect(x, y, width, height)

    if button_rect.collidepoint(mouse_pos):
        pygame.draw.rect(screen_surface, active_color, button_rect)
        if mouse_click[0] == 1 and action is not None:
            pygame.time.wait(200) 
            return action
    else:
        pygame.draw.rect(screen_surface, inactive_color, button_rect)

    text_surface = font.render(text, True, WHITE)
    text_rect = text_surface.get_rect(center=button_rect.center)
    screen_surface.blit(text_surface, text_rect)
    return None

def draw_player_model(screen_surface, current_time):
    display_color = BLUE
    if current_character_instance and current_time - current_character_instance.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR
    elif current_character_instance and current_time - current_character_instance.last_action_time < FLASH_DURATION:
        display_color = ACTION_FLASH_COLOR

    pygame.draw.rect(screen_surface, display_color, (100, 300, 80, 120))
    pygame.draw.circle(screen_surface, display_color, (140, 280), 30)
    pygame.draw.line(screen_surface, display_color, (140, 350), (100, 380), 5)
    pygame.draw.line(screen_surface, display_color, (140, 350), (180, 380), 5)
    pygame.draw.line(screen_surface, display_color, (140, 420), (120, 470), 5)
    pygame.draw.line(screen_surface, display_color, (140, 420), (160, 470), 5)

def draw_goblin_king_model(screen_surface, current_time, enemy_obj):
    display_color = GREEN
    if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR
    
    pygame.draw.rect(screen_surface, display_color, (600, 320, 90, 100))
    pygame.draw.circle(screen_surface, display_color, (645, 300), 35)
    pygame.draw.polygon(screen_surface, BROWN, [(645, 265), (630, 240), (660, 240)])
    pygame.draw.line(screen_surface, BLACK, (635, 290), (640, 290), 2)
    pygame.draw.line(screen_surface, BLACK, (650, 290), (655, 290), 2)
    pygame.draw.arc(screen_surface, BLACK, (635, 305, 20, 10), 0, 3.14, 2)
    pygame.draw.line(screen_surface, BROWN, (600, 350), (580, 330), 5)
    pygame.draw.line(screen_surface, BROWN, (690, 350), (710, 330), 5)
    pygame.draw.line(screen_surface, BROWN, (610, 420), (600, 460), 5)
    pygame.draw.line(screen_surface, BROWN, (680, 420), (690, 460), 5)

def draw_orc_warlord_model(screen_surface, current_time, enemy_obj):
    display_color = DARK_GRAY
    if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR

    pygame.draw.rect(screen_surface, display_color, (580, 280, 120, 180))
    pygame.draw.circle(screen_surface, display_color, (640, 260), 50)
    pygame.draw.polygon(screen_surface, YELLOW, [(640, 210), (620, 190), (660, 190)])
    pygame.draw.polygon(screen_surface, YELLOW, [(640, 210), (610, 180), (650, 180)])
    pygame.draw.line(screen_surface, RED, (620, 240), (630, 240), 3)
    pygame.draw.line(screen_surface, RED, (650, 240), (660, 240), 3)
    pygame.draw.line(screen_surface, BLACK, (630, 270), (650, 270), 3)
    pygame.draw.line(screen_surface, BROWN, (580, 350), (550, 330), 7)
    pygame.draw.line(screen_surface, BROWN, (700, 350), (730, 330), 7)
    pygame.draw.line(screen_surface, BROWN, (590, 460), (580, 500), 7)
    pygame.draw.line(screen_surface, BROWN, (690, 460), (700, 500), 7)

def draw_king_slime_model(screen_surface, current_time, enemy_obj):
    display_color = BLUE
    if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR

    pygame.draw.ellipse(screen_surface, display_color, (590, 300, 120, 150))
    pygame.draw.ellipse(screen_surface, LIGHT_GRAY, (620, 320, 20, 20))
    pygame.draw.ellipse(screen_surface, LIGHT_GRAY, (660, 320, 20, 20))
    pygame.draw.circle(screen_surface, WHITE, (630, 328), 5)
    pygame.draw.circle(screen_surface, WHITE, (670, 328), 5)
    pygame.draw.arc(screen_surface, BLACK, (620, 360, 60, 30), 0, 3.14, 2)
    pygame.draw.polygon(screen_surface, YELLOW, [(650, 280), (630, 250), (670, 250)])

def draw_dragon_hatchling_model(screen_surface, current_time, enemy_obj):
    display_color = PURPLE
    if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR

    pygame.draw.ellipse(screen_surface, display_color, (580, 300, 150, 100))
    pygame.draw.circle(screen_surface, display_color, (700, 290), 40)
    pygame.draw.ellipse(screen_surface, BLACK, (690, 300, 30, 20))
    pygame.draw.circle(screen_surface, YELLOW, (695, 280), 8)
    pygame.draw.circle(screen_surface, YELLOW, (710, 280), 8)
    pygame.draw.polygon(screen_surface, RED, [(580, 320), (520, 250), (590, 280)])
    pygame.draw.polygon(screen_surface, RED, [(730, 320), (790, 250), (720, 280)])
    pygame.draw.line(screen_surface, display_color, (600, 400), (590, 450), 5)
    pygame.draw.line(screen_surface, display_color, (680, 400), (690, 450), 5)

def draw_ancient_golem_model(screen_surface, current_time, enemy_obj):
    display_color = LIGHT_GRAY
    if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
        display_color = HIT_FLASH_COLOR

    pygame.draw.rect(screen_surface, display_color, (590, 280, 120, 180))
    pygame.draw.rect(screen_surface, display_color, (610, 230, 80, 60))
    pygame.draw.circle(screen_surface, RED, (630, 250), 10)
    pygame.draw.circle(screen_surface, RED, (670, 250), 10)
    pygame.draw.line(screen_surface, display_color, (590, 350), (540, 330), 10)
    pygame.draw.line(screen_surface, display_color, (710, 350), (760, 330), 10)
    pygame.draw.line(screen_surface, display_color, (610, 460), (590, 510), 10)
    pygame.draw.line(screen_surface, display_color, (690, 460), (710, 510), 10)

def draw_enemy_by_name(screen_surface, enemy_name, current_time, enemy_obj):
    if enemy_name == "Goblin King":
        draw_goblin_king_model(screen_surface, current_time, enemy_obj)
    elif enemy_name == "Orc Warlord":
        draw_orc_warlord_model(screen_surface, current_time, enemy_obj)
    elif enemy_name == "King Slime":
        draw_king_slime_model(screen_surface, current_time, enemy_obj)
    elif enemy_name == "Dragon Hatchling":
        draw_dragon_hatchling_model(screen_surface, current_time, enemy_obj)
    elif enemy_name == "Ancient Golem":
        draw_ancient_golem_model(screen_surface, current_time, enemy_obj)
    else:
        display_color = RED
        if enemy_obj and current_time - enemy_obj.last_hit_time < FLASH_DURATION:
            display_color = HIT_FLASH_COLOR

        pygame.draw.rect(screen_surface, display_color, (600, 300, 100, 150))
        pygame.draw.circle(screen_surface, display_color, (650, 280), 40)
        pygame.draw.polygon(screen_surface, display_color, [(650, 240), (620, 200), (680, 200)])
        pygame.draw.line(screen_surface, display_color, (600, 350), (570, 330), 5)
        pygame.draw.line(screen_surface, display_color, (700, 350), (730, 330), 5)

def draw_background(screen_surface):
    screen_surface.fill(DARK_GRAY)
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 100, 100), 50) 
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 180, 80), 30) 
    
def get_save_path():
    android_path = "/sdcard/Documents/"
    if os.path.exists(android_path) and os.access(android_path, os.W_OK):
        return android_path
    
    ios_path = os.path.expanduser("~/Documents/")
    if os.path.exists(ios_path) and os.access(ios_path, os.W_OK):
        return ios_path

    print("Lỗi: Không tìm thấy đường dẫn lưu khả dụng cho Android/iOS/Máy tính.")
    return None

def save_game_data():
    global current_character_instance, GLOBAL_PLAYER_PROFILE
    save_path = get_save_path()
    if save_path is None:
        print("Lưu dữ liệu không khả dụng do không tìm thấy đường dẫn.")
        return False

    file_path = os.path.join(save_path, SAVE_FILE_NAME)
    
    if current_character_instance:
        GLOBAL_PLAYER_PROFILE.update_character_data(current_character_instance)

    data_to_save = {
        "player_profile": GLOBAL_PLAYER_PROFILE.to_dict()
    }
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data_to_save, f, ensure_ascii=False, indent=4)
        print(f"Lưu dữ liệu thành công tại: {file_path}")
        return True
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")
        return False

def load_game_data():
    global GLOBAL_PLAYER_PROFILE
    save_path = get_save_path()
    if save_path is None:
        print("Tải dữ liệu không khả dụng do không tìm thấy đường dẫn.")
        return None

    file_path = os.path.join(save_path, SAVE_FILE_NAME)

    if not os.path.exists(file_path):
        print("Không tìm thấy file lưu dữ liệu.")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        profile_data = data.get("player_profile")
        if profile_data:
            loaded_profile = PlayerProfile.from_dict(profile_data)
            loaded_profile.check_unlocks() 
            print(f"Tải hồ sơ người chơi thành công (Cấp: {loaded_profile.total_level}).")
            return loaded_profile
        return None
    except Exception as e:
        print(f"Lỗi khi tải dữ liệu: {e}")
        return None

def end_game_screen(message, color):
    start_time = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.K_ESCAPE or event.type == pygame.KEYDOWN:
                return

        SCREEN.fill(BLACK)
        
        end_text_surface = FONT_LARGE.render(message, True, color)
        end_text_rect = end_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        SCREEN.blit(end_text_surface, end_text_rect)

        continue_text_surface = FONT_MEDIUM.render("Nhấn phím bất kỳ để quay về Menu chính", True, WHITE)
        continue_text_rect = continue_text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        SCREEN.blit(continue_text_surface, continue_text_rect)

        pygame.display.flip()

        if pygame.time.get_ticks() - start_time > END_SCREEN_DURATION:
            return

def choose_character_screen():
    global current_character_instance, GLOBAL_PLAYER_PROFILE
    running = True

    if not GLOBAL_PLAYER_PROFILE: 
        loaded_profile = load_game_data()
        if loaded_profile:
            GLOBAL_PLAYER_PROFILE = loaded_profile
        else:
            GLOBAL_PLAYER_PROFILE = PlayerProfile()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.K_ESCAPE: 
                return

        SCREEN.fill(BLACK)
        draw_background(SCREEN)

        title_text = FONT_LARGE.render("Chọn Nhân Vật", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_text_rect)

        y_offset_start = 150
        for i, base_char_template in enumerate(CHARACTER_DATA_BASE): 
            char_name = base_char_template.name
            is_unlocked = char_name in GLOBAL_PLAYER_PROFILE.unlocked_character_names
            
            char_display_instance = GLOBAL_PLAYER_PROFILE.get_character_instance(char_name)
            if not char_display_instance:
                char_display_instance = base_char_template
            
            display_color = WHITE if is_unlocked else DARK_GRAY
            
            y_offset = y_offset_start + i * 140 

            char_name_text = FONT_MEDIUM.render(f"{char_name}", True, display_color)
            SCREEN.blit(char_name_text, (50, y_offset))
            
            char_level_exp_text = FONT_SMALL.render(f"Cấp: {GLOBAL_PLAYER_PROFILE.total_level}", True, display_color)
            SCREEN.blit(char_level_exp_text, (50, y_offset + 40))
            
            char_stats_text = FONT_SMALL.render(f"HP: {char_display_instance.maxHp} | ATK: {char_display_instance.attack} | Mana: {char_display_instance.maxMana}", True, display_color)
            SCREEN.blit(char_stats_text, (50, y_offset + 70))
            
            char_skill_info_text = FONT_SMALL.render(f"Skill: {char_display_instance.skill['name']} (Dmg: {char_display_instance.skill_power_calc}, Mana: {char_display_instance.skill_mana_cost_calc}, CD: {char_display_instance.skill['cooldown_turns']} lượt)", True, display_color)
            SCREEN.blit(char_skill_info_text, (50, y_offset + 100))

            if is_unlocked:
                button_action = draw_button(SCREEN, f"Chọn", SCREEN_WIDTH - 180, y_offset + 30, 90, 50, BLUE, LIGHT_GRAY, i, FONT_MEDIUM)
                if button_action is not None:
                    selected_char_name = CHARACTER_DATA_BASE[button_action].name
                    current_character_instance = GLOBAL_PLAYER_PROFILE.get_character_instance(selected_char_name)
                    current_character_instance.reset_stats()
                    return 
            else:
                unlock_level = CHARACTER_UNLOCK_LEVELS.get(char_name, 999)
                locked_text = FONT_MEDIUM.render(f"Cần cấp {unlock_level}", True, RED)
                SCREEN.blit(locked_text, (SCREEN_WIDTH - 200, y_offset + 45))

        back_button_action = draw_button(SCREEN, "Quay lại", (SCREEN_WIDTH // 2) - 100, SCREEN_HEIGHT - 80, 200, 60, DARK_GRAY, LIGHT_GRAY, "back", FONT_MEDIUM)
        if back_button_action == "back":
            return

        pygame.display.flip()

def choose_boss_screen():
    global chosen_boss_index
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.K_ESCAPE: 
                return

        SCREEN.fill(BLACK)
        draw_background(SCREEN)

        title_text = FONT_LARGE.render("Chọn Boss", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_text_rect)

        for i, boss in enumerate(BOSS_DATA):
            y_offset = 150 + i * 100 

            boss_name_text = FONT_MEDIUM.render(f"Boss {i+1}: {boss.name}", True, WHITE)
            SCREEN.blit(boss_name_text, (50, y_offset))
            
            boss_stats_text = FONT_SMALL.render(f"HP: {boss.maxHp} | ATK: {boss.attack} | EXP: {boss.exp_reward}", True, WHITE)
            SCREEN.blit(boss_stats_text, (50, y_offset + 40))
            
            button_action = draw_button(SCREEN, f"Chọn", SCREEN_WIDTH - 180, y_offset + 30, 90, 50, RED, LIGHT_GRAY, i, FONT_MEDIUM)
            if button_action is not None:
                chosen_boss_index = button_action
                return 

        back_button_action = draw_button(SCREEN, "Quay lại", (SCREEN_WIDTH // 2) - 100, SCREEN_HEIGHT - 80, 200, 60, DARK_GRAY, LIGHT_GRAY, "back", FONT_MEDIUM)
        if back_button_action == "back":
            return

        pygame.display.flip()

def inventory_screen(): 
    global current_character_instance
    if not current_character_instance: 
        print("Lỗi: Không có nhân vật được chọn để mở balo.")
        return

    running = True
    selected_item_index = -1

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: 
                    return

        SCREEN.fill(BLACK)
        draw_background(SCREEN)

        title_text = FONT_LARGE.render("Balo & Trang Bị", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_text_rect)

        equip_x = 50
        equip_y = 120
        SCREEN.blit(FONT_MEDIUM.render("Trang bị:", True, WHITE), (equip_x, equip_y))
        
        weapon_name = current_character_instance.equipment['weapon'].name if current_character_instance.equipment['weapon'] else 'Trống'
        weapon_stats = ""
        if current_character_instance.equipment['weapon']:
            atk_bonus = current_character_instance.equipment['weapon'].stats_bonus.get('atk', 0)
            weapon_stats = f" (ATK +{atk_bonus})" if atk_bonus > 0 else ""
        weapon_text = FONT_SMALL.render(f"Vũ khí: {weapon_name}{weapon_stats}", True, WHITE)
        SCREEN.blit(weapon_text, (equip_x + 20, equip_y + 40))
        if current_character_instance.equipment['weapon']:
            if draw_button(SCREEN, "Bỏ", equip_x + 280, equip_y + 30, 60, 40, BROWN, ORANGE, "unequip_weapon", FONT_TINY) == "unequip_weapon":
                current_character_instance.unequip_item("weapon")

        armor_name = current_character_instance.equipment['armor'].name if current_character_instance.equipment['armor'] else 'Trống'
        armor_stats = ""
        if current_character_instance.equipment['armor']:
            hp_bonus = current_character_instance.equipment['armor'].stats_bonus.get('hp', 0)
            armor_stats = f" (HP +{hp_bonus})" if hp_bonus > 0 else ""
        armor_text = FONT_SMALL.render(f"Giáp: {armor_name}{armor_stats}", True, WHITE)
        SCREEN.blit(armor_text, (equip_x + 20, equip_y + 80))
        if current_character_instance.equipment['armor']:
            if draw_button(SCREEN, "Bỏ", equip_x + 280, equip_y + 70, 60, 40, BROWN, ORANGE, "unequip_armor", FONT_TINY) == "unequip_armor":
                current_character_instance.unequip_item("armor")

        inventory_x = 50
        inventory_y = equip_y + 160
        SCREEN.blit(FONT_MEDIUM.render("Balo:", True, WHITE), (inventory_x, inventory_y))

        item_display_y = inventory_y + 40
        for i, item in enumerate(current_character_instance.inventory):
            item_text_display = item.name
            if item.item_type in ["weapon", "armor"]:
                atk_bonus = item.stats_bonus.get('atk', 0)
                hp_bonus = item.stats_bonus.get('hp', 0)
                mana_bonus = item.stats_bonus.get('mana', 0)
                if atk_bonus > 0: item_text_display += f" (ATK +{atk_bonus})"
                if hp_bonus > 0: item_text_display += f" (HP +{hp_bonus})"
                if mana_bonus > 0: item_text_display += f" (Mana +{mana_bonus})"
            elif item.item_type == "consumable":
                if item.heal > 0: item_text_display += f" (Hồi HP: {item.heal}"
                if item.manaCost < 0: item_text_display += f" Hồi Mana: {-item.manaCost})"
                elif item.manaCost > 0: item_text_display += f" Tốn Mana: {item.manaCost})"

            item_text = FONT_SMALL.render(f"{i+1}. {item_text_display}", True, WHITE)
            SCREEN.blit(item_text, (inventory_x + 20, item_display_y + i * 30))

            if draw_button(SCREEN, "Chọn", inventory_x + 450, item_display_y + i * 30 - 5, 60, 30, DARK_GRAY, LIGHT_GRAY, i, FONT_TINY) == i:
                selected_item_index = i

            if selected_item_index == i:
                action_button_x = inventory_x + 520
                action_button_y = item_display_y + i * 30 - 5

                if item.item_type in ["weapon", "armor"]:
                    if draw_button(SCREEN, "Trang bị", action_button_x, action_button_y, 80, 30, BLUE, YELLOW, "equip", FONT_TINY) == "equip":
                        if current_character_instance.equip_item(i):
                            selected_item_index = -1
                elif item.item_type == "consumable":
                    if draw_button(SCREEN, "Sử dụng", action_button_x, action_button_y, 80, 30, GREEN, YELLOW, "use", FONT_TINY) == "use":
                        if current_character_instance.use_consumable(i):
                            selected_item_index = -1


        back_button_action = draw_button(SCREEN, "Quay lại", (SCREEN_WIDTH // 2) - 100, SCREEN_HEIGHT - 80, 200, 60, DARK_GRAY, LIGHT_GRAY, "back", FONT_MEDIUM)
        if back_button_action == "back":
            return

        pygame.display.flip()

def main_menu_screen():
    global current_character_instance, GLOBAL_PLAYER_PROFILE, chosen_boss_index
    running = True

    loaded_profile = load_game_data()
    if loaded_profile:
        GLOBAL_PLAYER_PROFILE = loaded_profile
    else:
        GLOBAL_PLAYER_PROFILE = PlayerProfile()

    if not current_character_instance:
        current_character_instance = GLOBAL_PLAYER_PROFILE.get_character_instance("conor")
        if not current_character_instance: 
             current_character_instance = Character("conor", 150, 25, 200, "Slash", 45, 25, 3)
             GLOBAL_PLAYER_PROFILE.update_character_data(current_character_instance)


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_game_data()
                pygame.quit()
                exit()

        SCREEN.fill(BLACK)
        draw_background(SCREEN) 

        title_text = FONT_LARGE.render("RPG Đơn Giản", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        SCREEN.blit(title_text, title_text_rect)

        level_exp_text = FONT_MEDIUM.render(f"Cấp độ tổng: {GLOBAL_PLAYER_PROFILE.total_level} | EXP: {GLOBAL_PLAYER_PROFILE.total_experience}/{GLOBAL_PLAYER_PROFILE.exp_to_next_total_level}", True, YELLOW)
        level_exp_rect = level_exp_text.get_rect(center=(SCREEN_WIDTH // 2, 180))
        SCREEN.blit(level_exp_text, level_exp_rect)

        start_game_action = draw_button(SCREEN, "Đánh boss", (SCREEN_WIDTH // 2) - 150, 250, 300, 70, GREEN, LIGHT_GRAY, "start", FONT_MEDIUM)
        if start_game_action == "start":
            choose_boss_screen() 
            if chosen_boss_index != -1: 
                main_game_screen(BOSS_DATA[chosen_boss_index]) 
                chosen_boss_index = -1
                save_game_data()

        choose_char_action = draw_button(SCREEN, "Chọn nhân vật", (SCREEN_WIDTH // 2) - 150, 350, 300, 70, BLUE, LIGHT_GRAY, "choose", FONT_MEDIUM)
        if choose_char_action == "choose":
            choose_character_screen()
            save_game_data()

        inventory_action = draw_button(SCREEN, "Balo", (SCREEN_WIDTH // 2) - 150, 450, 300, 70, BROWN, LIGHT_GRAY, "inventory", FONT_MEDIUM)
        if inventory_action == "inventory":
            inventory_screen() 
            save_game_data()

        exit_game_action = draw_button(SCREEN, "Thoát", (SCREEN_WIDTH // 2) - 150, 550, 300, 70, RED, LIGHT_GRAY, "exit", FONT_MEDIUM)
        if exit_game_action == "exit":
            save_game_data()
            pygame.quit()
            exit()

        pygame.display.flip()

def main_game_screen(selected_boss): 
    global current_character_instance
    current_round = 0
    
    enemy = Enemy(selected_boss.name, selected_boss.maxHp, selected_boss.attack, selected_boss.exp_reward)
    
    current_character_instance.reset_stats()

    game_messages = []

    def add_game_message(msg):
        game_messages.append((msg, pygame.time.get_ticks()))
        while len(game_messages) > 4: 
            game_messages.pop(0)

    add_game_message("3...")
    pygame.display.flip()
    pygame.time.wait(1000)
    add_game_message("2...")
    pygame.display.flip()
    pygame.time.wait(1000)
    add_game_message("1...")
    pygame.display.flip()
    pygame.time.wait(1000)
    add_game_message("CHIẾN ĐẤU BẮT ĐẦU!")
    pygame.display.flip()

    running = True
    while running:
        current_time_ms = pygame.time.get_ticks() 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_i:
                    inventory_screen()
                    GLOBAL_PLAYER_PROFILE.update_character_data(current_character_instance)
                    pygame.display.flip() 
                    continue

        SCREEN.fill(BLACK)
        draw_background(SCREEN)
        draw_player_model(SCREEN, current_time_ms) 
        draw_enemy_by_name(SCREEN, enemy.name, current_time_ms, enemy)

        player_name_text = FONT_SMALL.render(f"{current_character_instance.name} (Cấp {current_character_instance.level})", True, WHITE)
        SCREEN.blit(player_name_text, (50, 40))
        player_stats_text = FONT_SMALL.render(f"HP: {current_character_instance.hp}/{current_character_instance.maxHp} | Mana: {current_character_instance.mana}/{current_character_instance.maxMana}", True, WHITE)
        SCREEN.blit(player_stats_text, (50, 70))
        equipped_weapon = current_character_instance.equipment['weapon'].name if current_character_instance.equipment['weapon'] else "Không"
        equipped_armor = current_character_instance.equipment['armor'].name if current_character_instance.equipment['armor'] else "Không"
        equipment_text = FONT_TINY.render(f"Vũ khí: {equipped_weapon} | Giáp: {equipped_armor}", True, WHITE)
        SCREEN.blit(equipment_text, (50, 160))

        ENEMY_INFO_X_POS = SCREEN_WIDTH - 250 
        enemy_name_text = FONT_SMALL.render(f"{enemy.name}", True, WHITE)
        SCREEN.blit(enemy_name_text, (ENEMY_INFO_X_POS, 40)) 
        enemy_hp_text = FONT_SMALL.render(f"HP: {enemy.hp}/{enemy.maxHp}", True, WHITE)
        SCREEN.blit(enemy_hp_text, (ENEMY_INFO_X_POS, 70)) 

        HP_BAR_WIDTH = 200
        HP_BAR_HEIGHT = 20
        pygame.draw.rect(SCREEN, RED, (50, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (50, 100, int(HP_BAR_WIDTH * (current_character_instance.hp / current_character_instance.maxHp)), HP_BAR_HEIGHT))

        ENEMY_BAR_X_POS = SCREEN_WIDTH - 50 - HP_BAR_WIDTH 
        pygame.draw.rect(SCREEN, RED, (ENEMY_BAR_X_POS, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (ENEMY_BAR_X_POS, 100, int(HP_BAR_WIDTH * (enemy.hp / enemy.maxHp)), HP_BAR_HEIGHT))

        MANA_BAR_WIDTH = 200
        MANA_BAR_HEIGHT = 15
        pygame.draw.rect(SCREEN, BLUE, (50, 130, MANA_BAR_WIDTH, MANA_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, YELLOW, (50, 130, int(MANA_BAR_WIDTH * (current_character_instance.mana / current_character_instance.maxMana)), MANA_BAR_HEIGHT))

        active_messages = [msg for msg, timestamp in game_messages if current_time_ms - timestamp < MESSAGE_DURATION]
        for i, msg in enumerate(active_messages):
            msg_surface = FONT_SMALL.render(msg, True, WHITE)
            SCREEN.blit(msg_surface, (50, 190 + i * 30)) 

        current_round_text = FONT_MEDIUM.render(f"Vòng: {current_round}", True, WHITE)
        current_round_text_rect = current_round_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        SCREEN.blit(current_round_text, current_round_text_rect)

        skill_status = "Sẵn sàng" if current_character_instance.skill["current_cooldown"] == 0 else f"Hồi chiêu: {current_character_instance.skill['current_cooldown']} lượt"
        skill_info_text = FONT_SMALL.render(f"Kỹ năng: {current_character_instance.skill['name']} | {skill_status}", True, WHITE)
        
        BUTTON_WIDTH = 250 
        BUTTON_HEIGHT = 80
        BUTTON_MARGIN = 20
     
        start_x_buttons = 50
        attack_button_y = SCREEN_HEIGHT - (BUTTON_HEIGHT * 3 + BUTTON_MARGIN * 2) - 20
        action_performed = None 

        if draw_button(SCREEN, "Tấn công thường", start_x_buttons, attack_button_y, BUTTON_WIDTH, BUTTON_HEIGHT, ORANGE, YELLOW, "attack", FONT_MEDIUM):
            action_performed = "attack"
       
        skill_button_y = attack_button_y + BUTTON_HEIGHT + BUTTON_MARGIN
        skill_button_text = f"Skill ({current_character_instance.skill_mana_cost_calc} Mana)"
        if draw_button(SCREEN, skill_button_text, start_x_buttons, skill_button_y, BUTTON_WIDTH, BUTTON_HEIGHT, BLUE, YELLOW, "skill", FONT_MEDIUM):
            action_performed = "skill"

        heal_button_y = skill_button_y + BUTTON_HEIGHT + BUTTON_MARGIN
        heal_amount_calc = 20 + (current_character_instance.level - 1) * 3
        heal_damage_calc = 10 + (current_character_instance.level - 1) * 2
        heal_mana_cost = 5 + (current_character_instance.level - 1) * 1
        if draw_button(SCREEN, f"Hồi máu (+{heal_amount_calc} HP, -{heal_mana_cost} Mana, gây {heal_damage_calc} sát thương)", start_x_buttons, heal_button_y, BUTTON_WIDTH, BUTTON_HEIGHT, GREEN, LIGHT_GRAY, "old_heal", FONT_TINY):
            action_performed = "old_heal"

        inventory_button_x = start_x_buttons + BUTTON_WIDTH + BUTTON_MARGIN + 50
        inventory_button_y = heal_button_y
        inventory_button_action = draw_button(SCREEN, "Balo (I)", inventory_button_x, inventory_button_y, BUTTON_WIDTH, BUTTON_HEIGHT, BROWN, LIGHT_GRAY, "inventory_in_battle", FONT_MEDIUM)
        if inventory_button_action == "inventory_in_battle":
            inventory_screen()
            GLOBAL_PLAYER_PROFILE.update_character_data(current_character_instance)
            pygame.display.flip() 
            continue

        SCREEN.blit(skill_info_text, (start_x_buttons + BUTTON_WIDTH + BUTTON_MARGIN, skill_button_y + (BUTTON_HEIGHT / 2) - (skill_info_text.get_height() / 2)))

        if action_performed:
            if action_performed == "attack":
                damage_dealt = current_character_instance.attack
                enemy.take_damage(damage_dealt)
                current_character_instance.mana = min(current_character_instance.mana + current_character_instance.level, current_character_instance.maxMana)
                add_game_message(f"Bạn tấn công thường, gây {damage_dealt} sát thương.")
                add_game_message(f"Hồi phục {current_character_instance.level} Mana. Mana hiện tại: {current_character_instance.mana}")
                enemy.last_hit_time = current_time_ms 
                current_character_instance.last_action_time = current_time_ms 
            elif action_performed == "skill":
                if current_character_instance.skill["current_cooldown"] == 0 and current_character_instance.mana >= current_character_instance.skill_mana_cost_calc:
                    damage_dealt = current_character_instance.skill_power_calc
                    enemy.take_damage(damage_dealt)
                    current_character_instance.mana -= current_character_instance.skill_mana_cost_calc
                    current_character_instance.skill["current_cooldown"] = current_character_instance.skill["cooldown_turns"]
                    add_game_message(f"Bạn sử dụng kỹ năng {current_character_instance.skill['name']}, gây {damage_dealt} sát thương!")
                    enemy.last_hit_time = current_time_ms 
                    current_character_instance.last_action_time = current_time_ms 
                elif current_character_instance.skill["current_cooldown"] > 0:
                    add_game_message("Kỹ năng đang trong thời gian hồi chiêu!")
                    pygame.display.flip()
                    pygame.time.wait(MESSAGE_DURATION // 2)
                    continue 
                else: 
                    add_game_message(f"Không đủ Mana để sử dụng kỹ năng! Cần {current_character_instance.skill_mana_cost_calc} Mana.")
                    pygame.display.flip()
                    pygame.time.wait(MESSAGE_DURATION // 2) 
                    continue 
            elif action_performed == "old_heal":
                heal_amount = 20 + (current_character_instance.level - 1) * 3
                damage_dealt = 10 + (current_character_instance.level - 1) * 2
                heal_mana_cost = 5 + (current_character_instance.level - 1) * 1
                
                if current_character_instance.mana >= heal_mana_cost:
                    current_character_instance.hp = min(current_character_instance.hp + heal_amount, current_character_instance.maxHp)
                    current_character_instance.mana -= heal_mana_cost
                    enemy.take_damage(damage_dealt)
                    add_game_message(f"Bạn hồi {heal_amount} HP, tốn {heal_mana_cost} Mana và gây {damage_dealt} sát thương.")
                    current_character_instance.last_action_time = current_time_ms 
                    enemy.last_hit_time = current_time_ms 
                else:
                    add_game_message(f"Không đủ Mana để hồi máu! Cần {heal_mana_cost} Mana.")
                    pygame.display.flip()
                    pygame.time.wait(MESSAGE_DURATION // 2)
                    continue


            if enemy.hp <= 0:
                add_game_message(f"Bạn đã đánh bại {enemy.name}!")
                GLOBAL_PLAYER_PROFILE.add_exp(enemy.exp_reward) 
                add_game_message(f"Bạn nhận được {enemy.exp_reward} EXP!")
                
                if ALL_ITEMS:
                    new_item = random.choice(ALL_ITEMS)
                    current_character_instance.add_item(new_item)
                    add_game_message(f"Bạn nhặt được: {new_item.name}!")
                
                pygame.display.flip()
                pygame.time.wait(MESSAGE_DURATION)
                end_game_screen("YOU WIN!", GREEN) 
                return 

            current_round += 1
            if current_character_instance.skill["current_cooldown"] > 0:
                current_character_instance.skill["current_cooldown"] -= 1
            
            enemy_action = enemy.get_action(current_character_instance.hp)
            if enemy_action == "heal":
                heal_amount = 25 
                enemy.heal(heal_amount)
                damage_to_player = 20 
                current_character_instance.hp -= damage_to_player
                add_game_message(f"{enemy.name} hồi máu +{heal_amount}! Ma thuật gây {damage_to_player} sát thương!")
            elif enemy_action == "critical_attack":
                damage_to_player = enemy.attack + 15 
                current_character_instance.hp -= damage_to_player
                add_game_message(f"{enemy.name} ra đòn chí mạng! Gây {damage_to_player} sát thương!")
            else:
                damage_to_player = enemy.attack
                current_character_instance.hp -= damage_to_player
                add_game_message(f"{enemy.name} tấn công thường! Gây {damage_to_player} sát thương!")

            current_character_instance.last_hit_time = current_time_ms 
            pygame.display.flip()
            pygame.time.wait(300)

            if current_character_instance.hp <= 0:
                add_game_message(f"Bạn đã bị đánh bại bởi {enemy.name}...")
                pygame.display.flip()
                pygame.time.wait(MESSAGE_DURATION)
                end_game_screen("GAME OVER!", RED) 
                return 
        
 
        pygame.display.flip()

if __name__ == "__main__":
    main_menu_screen()
