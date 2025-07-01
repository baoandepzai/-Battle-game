import pygame
import time

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

try:
    FONT_PATH = "/sdcard/Documents/Arial.ttf"  
    FONT_LARGE = pygame.font.Font(FONT_PATH, 74)
    FONT_MEDIUM = pygame.font.Font(FONT_PATH, 30)
    FONT_SMALL = pygame.font.Font(FONT_PATH, 25)
    FONT_TINY = pygame.font.Font(FONT_PATH, 20)
except pygame.error:
    print(f"Lỗi: Không tìm thấy font '{FONT_PATH}'. Vui lòng đảm bảo file font nằm đúng vị trí.")
    print("Sử dụng font mặc định của Pygame (có thể không hỗ trợ tiếng Việt đầy đủ).")
    FONT_LARGE = pygame.font.Font(None, 74)
    FONT_MEDIUM = pygame.font.Font(None, 40)
    FONT_SMALL = pygame.font.Font(None, 25)
    FONT_TINY = pygame.font.Font(None, 20)

ENEMY_MAX_HP = 500
MESSAGE_DURATION = 3000 
END_SCREEN_DURATION = 3000 

current_character_index = 0 

class Character:
    def __init__(self, name, hp, atk, max_mana, skill_name, skill_power, skill_mana_cost, skill_cooldown_turns):
        self.name = name
        self.max_hp = hp
        self.current_hp = hp
        self.attack = atk
        self.max_mana = max_mana
        self.current_mana = max_mana
        self.skill = {
            "name": skill_name,
            "power": skill_power,
            "mana_cost": skill_mana_cost,
            "cooldown_turns": skill_cooldown_turns,
            "current_cooldown": 0
        }

    def reset_stats(self):
        self.current_hp = self.max_hp
        self.current_mana = self.max_mana
        self.skill["current_cooldown"] = 0

CHARACTER_DATA = [
    Character("conor", 150, 25, 200, "Slash", 45, 25, 3),
    Character("savior", 200, 20, 200, "Roar", 40, 20, 2),
    Character("justice", 125, 30, 250, "Fireball", 60, 30, 4)
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

def draw_player_model(screen_surface):
    pygame.draw.rect(screen_surface, BLUE, (100, 300, 80, 120))
    pygame.draw.circle(screen_surface, BLUE, (140, 280), 30)
    pygame.draw.line(screen_surface, BLUE, (140, 350), (100, 380), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 350), (180, 380), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 420), (120, 470), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 420), (160, 470), 5)

def draw_enemy_model(screen_surface):
    pygame.draw.rect(screen_surface, RED, (600, 300, 100, 150))
    pygame.draw.circle(screen_surface, RED, (650, 280), 40)
    pygame.draw.polygon(screen_surface, RED, [(650, 240), (620, 200), (680, 200)])
    pygame.draw.line(screen_surface, RED, (600, 350), (570, 330), 5)
    pygame.draw.line(screen_surface, RED, (700, 350), (730, 330), 5)

def draw_background(screen_surface):
    screen_surface.fill(DARK_GRAY)
    pygame.draw.rect(screen_surface, GREEN, (0, SCREEN_HEIGHT - -10, SCREEN_WIDTH, 100))
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 100, 100), 50) 
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 180, 80), 30) 
    
def enemy_AI_logic(enemy_current_hp, player_current_hp):
    if enemy_current_hp < 50 and enemy_current_hp > 0:
        return 1 
    elif player_current_hp < 35:
        return 2 
    else:
        return 3 

def end_game_screen(message, color):
    start_time = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN: 
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
    global current_character_index
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        SCREEN.fill(BLACK)
        draw_background(SCREEN)

        title_text = FONT_LARGE.render("Chọn Nhân Vật", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_text_rect)

        for i, char in enumerate(CHARACTER_DATA):
            y_offset = 150 + i * 140 

            char_name_text = FONT_MEDIUM.render(f"Nhân vật {i+1}: {char.name}", True, WHITE)
            SCREEN.blit(char_name_text, (50, y_offset))
            
            char_stats_text = FONT_SMALL.render(f"HP: {char.max_hp} | ATK: {char.attack} | Mana: {char.max_mana}", True, WHITE)
            SCREEN.blit(char_stats_text, (50, y_offset + 40))
            
            char_skill_text = FONT_SMALL.render(f"Kỹ năng: {char.skill['name']} (ST: {char.skill['power']}, Mana: {char.skill['mana_cost']})", True, WHITE)
            SCREEN.blit(char_skill_text, (50, y_offset + 70))

            button_action = draw_button(SCREEN, f"Chọn", SCREEN_WIDTH - 180, y_offset + 30, 150, 50, BLUE, LIGHT_GRAY, i, FONT_MEDIUM)
            if button_action is not None:
                current_character_index = button_action
                CHARACTER_DATA[current_character_index].reset_stats() 
                return 

        pygame.display.flip()

def main_menu_screen():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        SCREEN.fill(BLACK)
        draw_background(SCREEN) 

        title_text = FONT_LARGE.render("RPG Đơn Giản", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        SCREEN.blit(title_text, title_text_rect)

        start_game_action = draw_button(SCREEN, "Bắt đầu trò chơi", (SCREEN_WIDTH // 2) - 150, 250, 300, 70, GREEN, LIGHT_GRAY, "start", FONT_MEDIUM)
        if start_game_action == "start":
            main_game_screen(current_character_index)

        choose_char_action = draw_button(SCREEN, "Chọn nhân vật", (SCREEN_WIDTH // 2) - 150, 350, 300, 70, BLUE, LIGHT_GRAY, "choose", FONT_MEDIUM)
        if choose_char_action == "choose":
            choose_character_screen()

        exit_game_action = draw_button(SCREEN, "Thoát", (SCREEN_WIDTH // 2) - 150, 450, 300, 70, RED, LIGHT_GRAY, "exit", FONT_MEDIUM)
        if exit_game_action == "exit":
            pygame.quit()
            exit()

        pygame.display.flip()

def main_game_screen(char_idx):
    current_round = 0
    enemy_current_hp = ENEMY_MAX_HP
    player_char = CHARACTER_DATA[char_idx]

    player_char.reset_stats()

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

        SCREEN.fill(BLACK)
        draw_background(SCREEN)
        draw_player_model(SCREEN)
        draw_enemy_model(SCREEN)

        player_name_text = FONT_SMALL.render(f"{player_char.name}", True, WHITE)
        SCREEN.blit(player_name_text, (50, 40))
        player_stats_text = FONT_SMALL.render(f"HP: {player_char.current_hp} | Mana: {player_char.current_mana}/{player_char.max_mana}", True, WHITE)
        SCREEN.blit(player_stats_text, (50, 70))

        ENEMY_INFO_X_POS = SCREEN_WIDTH - 250 
        enemy_name_text = FONT_SMALL.render(f"Kẻ địch", True, WHITE)
        SCREEN.blit(enemy_name_text, (ENEMY_INFO_X_POS, 40)) 
        enemy_hp_text = FONT_SMALL.render(f"HP: {enemy_current_hp}", True, WHITE)
        SCREEN.blit(enemy_hp_text, (ENEMY_INFO_X_POS, 70)) 

        HP_BAR_WIDTH = 200
        HP_BAR_HEIGHT = 20

        pygame.draw.rect(SCREEN, RED, (50, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (50, 100, int(HP_BAR_WIDTH * (player_char.current_hp / player_char.max_hp)), HP_BAR_HEIGHT))

        ENEMY_BAR_X_POS = SCREEN_WIDTH - 50 - HP_BAR_WIDTH 
        pygame.draw.rect(SCREEN, RED, (ENEMY_BAR_X_POS, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (ENEMY_BAR_X_POS, 100, int(HP_BAR_WIDTH * (enemy_current_hp / ENEMY_MAX_HP)), HP_BAR_HEIGHT))

        MANA_BAR_WIDTH = 200
        MANA_BAR_HEIGHT = 15
        pygame.draw.rect(SCREEN, BLUE, (50, 130, MANA_BAR_WIDTH, MANA_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, YELLOW, (50, 130, int(MANA_BAR_WIDTH * (player_char.current_mana / player_char.max_mana)), MANA_BAR_HEIGHT))

        active_messages = [msg for msg, timestamp in game_messages if current_time_ms - timestamp < MESSAGE_DURATION]
        for i, msg in enumerate(active_messages):
            msg_surface = FONT_SMALL.render(msg, True, WHITE)
            SCREEN.blit(msg_surface, (50, 180 + i * 30))

        current_round_text = FONT_MEDIUM.render(f"Vòng: {current_round}", True, WHITE)
        current_round_text_rect = current_round_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        SCREEN.blit(current_round_text, current_round_text_rect)

        skill_status = "Sẵn sàng" if player_char.skill["current_cooldown"] == 0 else f"Hồi chiêu: {player_char.skill['current_cooldown']} lượt"
        skill_info_text = FONT_SMALL.render(f"Kỹ năng: {player_char.skill['name']} | {skill_status}", True, WHITE)
        
        BUTTON_WIDTH = 260
        BUTTON_HEIGHT = 60
        BUTTON_MARGIN = 10
     
        start_y_buttons = SCREEN_HEIGHT - (BUTTON_HEIGHT * 3 + BUTTON_MARGIN * 2) - 20 

        action_performed = None 

        if draw_button(SCREEN, "Tấn công thường", 50, start_y_buttons, BUTTON_WIDTH, BUTTON_HEIGHT, ORANGE, YELLOW, "attack", FONT_MEDIUM):
            action_performed = "attack"
       
        skill_button_text = f"Skill ({player_char.skill['mana_cost']} Mana)"
        if draw_button(SCREEN, skill_button_text, 50, start_y_buttons + BUTTON_HEIGHT + BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT, BLUE, YELLOW, "skill", FONT_MEDIUM):
            action_performed = "skill"
        
        heal_button_text = "Hồi phục (10 Mana)"
        if draw_button(SCREEN, heal_button_text, 50, start_y_buttons + (BUTTON_HEIGHT + BUTTON_MARGIN) * 2, BUTTON_WIDTH, BUTTON_HEIGHT, GREEN, YELLOW, "heal", FONT_MEDIUM):
            action_performed = "heal"
        
        SCREEN.blit(skill_info_text, (50 + BUTTON_WIDTH + 30, start_y_buttons + BUTTON_HEIGHT / 2 - skill_info_text.get_height() / 2))

        if action_performed:

            if action_performed == "attack":
                add_game_message(f"Bạn tấn công thường, gây {player_char.attack} sát thương.")
                enemy_current_hp -= player_char.attack
                player_char.current_mana = min(player_char.current_mana + 5, player_char.max_mana)
                add_game_message(f"Hồi phục 5 Mana. Mana hiện tại: {player_char.current_mana}")
            elif action_performed == "skill":
                if player_char.skill["current_cooldown"] == 0 and player_char.current_mana >= player_char.skill["mana_cost"]:
                    add_game_message(f"Bạn sử dụng kỹ năng {player_char.skill['name']}, gây {player_char.skill['power']} sát thương!")
                    enemy_current_hp -= player_char.skill["power"]
                    player_char.current_mana -= player_char.skill["mana_cost"]
                    player_char.skill["current_cooldown"] = player_char.skill["cooldown_turns"]
                elif player_char.skill["current_cooldown"] > 0:
                    add_game_message("Kỹ năng đang trong thời gian hồi chiêu!")
                    # Dòng 'continue' này bị lặp, loại bỏ để không bỏ qua các logic tiếp theo
                    # add_game_message(f"Không đủ Mana để sử dụng kỹ năng! Cần {player_char.skill['mana_cost']} Mana.")
                    # continue 
                else: # Thêm điều kiện này để xử lý trường hợp không đủ mana
                    add_game_message(f"Không đủ Mana để sử dụng kỹ năng! Cần {player_char.skill['mana_cost']} Mana.")
                    continue # Giữ continue ở đây nếu bạn muốn bỏ qua lượt
            elif action_performed == "heal":
                if player_char.current_mana >= 10: 
                    player_char.current_hp += 20
                    player_char.current_mana -= 10
                    enemy_current_hp -= 10 
                    add_game_message(f"Bạn hồi phục 20 HP và gây ra 10 sát thương.")
                else:
                    add_game_message("Không đủ mana để hồi phục! Cần 10 Mana.")
                    continue 
            
            # Kiểm tra chiến thắng/thua sau khi hành động của người chơi và kẻ địch
            if enemy_current_hp <= 0:
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return
                
            current_round += 1
            if player_char.skill["current_cooldown"] > 0:
                player_char.skill["current_cooldown"] -= 1
            
            enemy_action = enemy_AI_logic(enemy_current_hp, player_char.current_hp)
            if enemy_action == 1:
                enemy_current_hp += 25
                player_char.current_hp -= 10
                add_game_message("Kẻ địch Hồi máu +25! Ma thuật gây 10 sát thương!")
            elif enemy_action == 2:
                player_char.current_hp -= 20
                add_game_message("Kẻ địch ra đòn chí mạng! Gây 20 sát thương!")
            else:
                player_char.current_hp -= 15
                add_game_message("Kẻ địch tấn công thường! Gây 15 sát thương!")

            if player_char.current_hp <= 0:
                end_game_screen("GAME OVER!", RED) 
                main_menu_screen()
                return
            
            if enemy_current_hp <= 0: 
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return 
        
        pygame.display.flip()

if __name__ == "__main__":
    main_menu_screen()
          add_game_message("Không đủ mana để hồi phục! Cần 10 Mana.")
                    continue 
            
            if enemy_current_hp <= 0:
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return
                
            current_round += 1
            if player_char.skill["current_cooldown"] > 0:
                player_char.skill["current_cooldown"] -= 1
            
            enemy_action = enemy_AI_logic(enemy_current_hp, player_char.current_hp)
            if enemy_action == 1:
                enemy_current_hp += 25
                player_char.current_hp -= 10
                add_game_message("Kẻ địch Hồi máu +25! Ma thuật gây 10 sát thương!")
            elif enemy_action == 2:
                player_char.current_hp -= 20
                add_game_message("Kẻ địch ra đòn chí mạng! Gây 20 sát thương!")
            else:
                player_char.current_hp -= 15
                add_game_message("Kẻ địch tấn công thường! Gây 15 sát thương!")

            if player_char.current_hp <= 0:
                end_game_screen("GAME OVER!", RED) 
                main_menu_screen()
                return
            
            if enemy_current_hp <= 0: 
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return 
        
        pygame.display.flip()

if __name__ == "__main__":
    main_menu_screen()
(, 20, 2),
    Character("justice", 125, 30, 250, "Fireball", 60, 30, 4)
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

def draw_player_model(screen_surface):
    pygame.draw.rect(screen_surface, BLUE, (100, 300, 80, 120))
    pygame.draw.circle(screen_surface, BLUE, (140, 280), 30)
    pygame.draw.line(screen_surface, BLUE, (140, 350), (100, 380), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 350), (180, 380), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 420), (120, 470), 5)
    pygame.draw.line(screen_surface, BLUE, (140, 420), (160, 470), 5)

def draw_enemy_model(screen_surface):
    pygame.draw.rect(screen_surface, RED, (600, 300, 100, 150))
    pygame.draw.circle(screen_surface, RED, (650, 280), 40)
    pygame.draw.polygon(screen_surface, RED, [(650, 240), (620, 200), (680, 200)])
    pygame.draw.line(screen_surface, RED, (600, 350), (570, 330), 5)
    pygame.draw.line(screen_surface, RED, (700, 350), (730, 330), 5)

def draw_background(screen_surface):
    screen_surface.fill(DARK_GRAY)
    pygame.draw.rect(screen_surface, GREEN, (0, SCREEN_HEIGHT - -10, SCREEN_WIDTH, 100))
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 100, 100), 50) 
    pygame.draw.circle(screen_surface, LIGHT_GRAY, (SCREEN_WIDTH - 180, 80), 30) 
    
def enemy_AI_logic(enemy_current_hp, player_current_hp):
    if enemy_current_hp < 50 and enemy_current_hp > 0:
        return 1 
    elif player_current_hp < 35:
        return 2 
    else:
        return 3 

def end_game_screen(message, color):
    start_time = pygame.time.get_ticks()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN: 
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
    global current_character_index
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        SCREEN.fill(BLACK)
        draw_background(SCREEN)

        title_text = FONT_LARGE.render("Chọn Nhân Vật", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        SCREEN.blit(title_text, title_text_rect)

        for i, char in enumerate(CHARACTER_DATA):
            y_offset = 150 + i * 140 

            char_name_text = FONT_MEDIUM.render(f"Nhân vật {i+1}: {char.name}", True, WHITE)
            SCREEN.blit(char_name_text, (50, y_offset))
            
            char_stats_text = FONT_SMALL.render(f"HP: {char.max_hp} | ATK: {char.attack} | Mana: {char.max_mana}", True, WHITE)
            SCREEN.blit(char_stats_text, (50, y_offset + 40))
            
            char_skill_text = FONT_SMALL.render(f"Kỹ năng: {char.skill['name']} (ST: {char.skill['power']}, Mana: {char.skill['mana_cost']})", True, WHITE)
            SCREEN.blit(char_skill_text, (50, y_offset + 70))

            button_action = draw_button(SCREEN, f"Chọn", SCREEN_WIDTH - 180, y_offset + 30, 150, 50, BLUE, LIGHT_GRAY, i, FONT_MEDIUM)
            if button_action is not None:
                current_character_index = button_action
                CHARACTER_DATA[current_character_index].reset_stats() 
                return 

        pygame.display.flip()

def main_menu_screen():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

        SCREEN.fill(BLACK)
        draw_background(SCREEN) 

        title_text = FONT_LARGE.render("RPG Đơn Giản", True, WHITE)
        title_text_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        SCREEN.blit(title_text, title_text_rect)

        start_game_action = draw_button(SCREEN, "Bắt đầu trò chơi", (SCREEN_WIDTH // 2) - 150, 250, 300, 70, GREEN, LIGHT_GRAY, "start", FONT_MEDIUM)
        if start_game_action == "start":
            main_game_screen(current_character_index)

        choose_char_action = draw_button(SCREEN, "Chọn nhân vật", (SCREEN_WIDTH // 2) - 150, 350, 300, 70, BLUE, LIGHT_GRAY, "choose", FONT_MEDIUM)
        if choose_char_action == "choose":
            choose_character_screen()

        exit_game_action = draw_button(SCREEN, "Thoát", (SCREEN_WIDTH // 2) - 150, 450, 300, 70, RED, LIGHT_GRAY, "exit", FONT_MEDIUM)
        if exit_game_action == "exit":
            pygame.quit()
            exit()

        pygame.display.flip()

def main_game_screen(char_idx):
    current_round = 0
    enemy_current_hp = ENEMY_MAX_HP
    player_char = CHARACTER_DATA[char_idx]

    player_char.reset_stats()

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

        SCREEN.fill(BLACK)
        draw_background(SCREEN)
        draw_player_model(SCREEN)
        draw_enemy_model(SCREEN)

        player_name_text = FONT_SMALL.render(f"{player_char.name}", True, WHITE)
        SCREEN.blit(player_name_text, (50, 40))
        player_stats_text = FONT_SMALL.render(f"HP: {player_char.current_hp} | Mana: {player_char.current_mana}/{player_char.max_mana}", True, WHITE)
        SCREEN.blit(player_stats_text, (50, 70))

        ENEMY_INFO_X_POS = SCREEN_WIDTH - 250 
        enemy_name_text = FONT_SMALL.render(f"Kẻ địch", True, WHITE)
        SCREEN.blit(enemy_name_text, (ENEMY_INFO_X_POS, 40)) 
        enemy_hp_text = FONT_SMALL.render(f"HP: {enemy_current_hp}", True, WHITE)
        SCREEN.blit(enemy_hp_text, (ENEMY_INFO_X_POS, 70)) 

        HP_BAR_WIDTH = 200
        HP_BAR_HEIGHT = 20

        pygame.draw.rect(SCREEN, RED, (50, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (50, 100, int(HP_BAR_WIDTH * (player_char.current_hp / player_char.max_hp)), HP_BAR_HEIGHT))

        ENEMY_BAR_X_POS = SCREEN_WIDTH - 50 - HP_BAR_WIDTH 
        pygame.draw.rect(SCREEN, RED, (ENEMY_BAR_X_POS, 100, HP_BAR_WIDTH, HP_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, GREEN, (ENEMY_BAR_X_POS, 100, int(HP_BAR_WIDTH * (enemy_current_hp / ENEMY_MAX_HP)), HP_BAR_HEIGHT))

        MANA_BAR_WIDTH = 200
        MANA_BAR_HEIGHT = 15
        pygame.draw.rect(SCREEN, BLUE, (50, 130, MANA_BAR_WIDTH, MANA_BAR_HEIGHT))
        pygame.draw.rect(SCREEN, YELLOW, (50, 130, int(MANA_BAR_WIDTH * (player_char.current_mana / player_char.max_mana)), MANA_BAR_HEIGHT))

        active_messages = [msg for msg, timestamp in game_messages if current_time_ms - timestamp < MESSAGE_DURATION]
        for i, msg in enumerate(active_messages):
            msg_surface = FONT_SMALL.render(msg, True, WHITE)
            SCREEN.blit(msg_surface, (50, 180 + i * 30))

        current_round_text = FONT_MEDIUM.render(f"Vòng: {current_round}", True, WHITE)
        current_round_text_rect = current_round_text.get_rect(center=(SCREEN_WIDTH // 2, 200))
        SCREEN.blit(current_round_text, current_round_text_rect)

        skill_status = "Sẵn sàng" if player_char.skill["current_cooldown"] == 0 else f"Hồi chiêu: {player_char.skill['current_cooldown']} lượt"
        skill_info_text = FONT_SMALL.render(f"Kỹ năng: {player_char.skill['name']} | {skill_status}", True, WHITE)
        
        BUTTON_WIDTH = 260
        BUTTON_HEIGHT = 60
        BUTTON_MARGIN = 10
     
        start_y_buttons = SCREEN_HEIGHT - (BUTTON_HEIGHT * 3 + BUTTON_MARGIN * 2) - 20 

        action_performed = None 

        if draw_button(SCREEN, "Tấn công thường", 50, start_y_buttons, BUTTON_WIDTH, BUTTON_HEIGHT, ORANGE, YELLOW, "attack", FONT_MEDIUM):
            action_performed = "attack"
       
        skill_button_text = f"Skill ({player_char.skill['mana_cost']} Mana)"
        if draw_button(SCREEN, skill_button_text, 50, start_y_buttons + BUTTON_HEIGHT + BUTTON_MARGIN, BUTTON_WIDTH, BUTTON_HEIGHT, BLUE, YELLOW, "skill", FONT_MEDIUM):
            action_performed = "skill"
        
        heal_button_text = "Hồi phục (10 Mana)"
        if draw_button(SCREEN, heal_button_text, 50, start_y_buttons + (BUTTON_HEIGHT + BUTTON_MARGIN) * 2, BUTTON_WIDTH, BUTTON_HEIGHT, GREEN, YELLOW, "heal", FONT_MEDIUM):
            action_performed = "heal"
        
        SCREEN.blit(skill_info_text, (50 + BUTTON_WIDTH + 30, start_y_buttons + BUTTON_HEIGHT / 2 - skill_info_text.get_height() / 2))

        if action_performed:

            if action_performed == "attack":
                add_game_message(f"Bạn tấn công thường, gây {player_char.attack} sát thương.")
                enemy_current_hp -= player_char.attack
                player_char.current_mana = min(player_char.current_mana + 5, player_char.max_mana)
                add_game_message(f"Hồi phục 5 Mana. Mana hiện tại: {player_char.current_mana}")
            elif action_performed == "skill":
                if player_char.skill["current_cooldown"] == 0 and player_char.current_mana >= player_char.skill["mana_cost"]:
                    add_game_message(f"Bạn sử dụng kỹ năng {player_char.skill['name']}, gây {player_char.skill['power']} sát thương!")
                    enemy_current_hp -= player_char.skill["power"]
                    player_char.current_mana -= player_char.skill["mana_cost"]
                    player_char.skill["current_cooldown"] = player_char.skill["cooldown_turns"]
                elif player_char.skill["current_cooldown"] > 0:
                    add_game_message("Kỹ năng đang trong thời gian hồi chiêu!")
                    continue 
                    add_game_message(f"Không đủ Mana để sử dụng kỹ năng! Cần {player_char.skill['mana_cost']} Mana.")
                    continue 
            elif action_performed == "heal":
                if player_char.current_mana >= 10: 
                    player_char.current_hp += 20
                    player_char.current_mana -= 10
                    enemy_current_hp -= 10 
                    add_game_message(f"Bạn hồi phục 20 HP và gây ra 10 sát thương.")
                else:
                    add_game_message("Không đủ mana để hồi phục! Cần 10 Mana.")
                    continue 
            
            if enemy_current_hp <= 0:
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return
                
            current_round += 1
            if player_char.skill["current_cooldown"] > 0:
                player_char.skill["current_cooldown"] -= 1
            
            enemy_action = enemy_AI_logic(enemy_current_hp, player_char.current_hp)
            if enemy_action == 1:
                enemy_current_hp += 25
                player_char.current_hp -= 10
                add_game_message("Kẻ địch Hồi máu +25! Ma thuật gây 10 sát thương!")
            elif enemy_action == 2:
                player_char.current_hp -= 20
                add_game_message("Kẻ địch ra đòn chí mạng! Gây 20 sát thương!")
            else:
                player_char.current_hp -= 15
                add_game_message("Kẻ địch tấn công thường! Gây 15 sát thương!")

            if player_char.current_hp <= 0:
                end_game_screen("GAME OVER!", RED) 
                main_menu_screen()
                return
            
            if enemy_current_hp <= 0: 
                end_game_screen("YOU WIN!", GREEN) 
                main_menu_screen()
                return 
        
        pygame.display.flip()

if __name__ == "__main__":
    main_menu_screen()
