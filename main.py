# main.py (v9.1.0 - Dragon Quest Special Edition - Based on v8.2.16)
# -*- coding: utf-8 -*-

import pygame
import random
import sys
import os
import time
import math
import asyncio

# --- 基本設定 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GAME_TITLE = "Dragon Quest特別版" # MODIFIED

# --- 顏色 ---
BLACK = (0, 0, 0); WHITE = (255, 255, 255); RED = (255, 0, 0); GREEN = (0, 255, 0); BLUE = (0, 0, 255); YELLOW = (255, 255, 0); ORANGE = (255, 165, 0); PURPLE = (128, 0, 128); CYAN = (0, 255, 255); MAGENTA = (255, 0, 255)

# --- 玩家設定 ---
PLAYER_INITIAL_SHOOT_DELAY = 250
PLAYER_INITIAL_LIVES = 3
PLAYER_INITIAL_SKILL_CHARGES = 1 # MODIFIED: Renamed from POM_CHARGES for clarity in DQ theme
PLAYER_SCORE_PER_LIFE = 1000
PLAYER_INVINCIBILITY_DURATION = 2000

# --- 技能設定 ---
TRIPLE_CLICK_INTERVAL = 2.0
SKILL_DAMAGE = 4 # MODIFIED: Renamed from POMERANIAN_DAMAGE

# --- 資源路徑 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# --- 使用者指定的資料夾名稱 ---
IMG_DIR = os.path.join(BASE_DIR, 'img') # Using 'img' as per user's structure
SND_DIR = os.path.join(BASE_DIR, 'snd') # Using 'snd' as per user's structure
FONT_DIR = os.path.join(BASE_DIR, 'fonts') # Assuming 'fonts' for custom font

# --- 全螢幕相關 ---
is_fullscreen = False
fullscreen_button_rect = None
FULLSCREEN_BUTTON_COLOR = BLUE
FULLSCREEN_BUTTON_TEXT_COLOR = WHITE
FULLSCREEN_BUTTON_SIZE = (30, 30)
FULLSCREEN_BUTTON_MARGIN = 5

# --- Asset Loading Variables ---
assets = {}
sounds = {}
background_sound = None # Use a Sound object for BGM
cover_sound = None # MODIFIED: For cover music (dq.ogg)
main_font_path = None

# --- Asset Loading Function ---
def load_assets():
    print("開始載入圖片資源...")
    # Keeping original filenames as per user request for "套皮"
    img_files = {
        'player': 'zg.png', 'skill_icon': 'bog01.png', 'skill_anim1': 'bog02.png', # MODIFIED: Renamed keys for clarity
        'skill_anim2': 'bog03.png', 'cover': 'start_screen.jpg'
    }
    img_files.update({f'p{i:02d}': f'p{i:02d}.png' for i in range(1, 10)})
    img_files.update({f'boss{i*10}': f'boss{i*10}.png' for i in range(1, 6)})
    for key, filename in img_files.items():
        path = os.path.join(IMG_DIR, filename); assets[key] = None
        if not os.path.exists(path): print(f"  錯誤：檔案不存在 {filename} 在路徑 {path}"); continue
        try:
            image = pygame.image.load(path)
            try: assets[key] = image.convert_alpha()
            except ValueError: assets[key] = image.convert()
        except Exception as e: print(f"  錯誤：載入圖片 {filename}: {e}"); assets[key] = None

    # Fallback for skill animation images if missing, using skill_icon or placeholder
    if not assets.get('skill_anim1') or not assets.get('skill_anim2'):
        print("警告: 缺少技能動畫圖，使用備用圖。")
        if not assets.get('skill_anim1') and assets.get('skill_icon'): assets['skill_anim1'] = assets['skill_icon']
        if not assets.get('skill_anim2') and assets.get('skill_anim1'): assets['skill_anim2'] = assets['skill_anim1']
        elif not assets.get('skill_anim2') and assets.get('skill_icon'): assets['skill_anim2'] = assets['skill_icon']

    if assets.get('player') is None:
        print("警告: 無玩家圖, 使用備用"); assets['player_fallback'] = pygame.Surface([50, 60]); assets['player_fallback'].fill(GREEN); assets['player'] = assets['player_fallback']
    if assets.get('cover'):
        try: assets['cover'] = pygame.transform.scale(assets['cover'], (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e: print(f"錯誤: 縮放封面失敗: {e}"); assets['cover'] = None
    print("圖片資源載入完成.")

# --- 音效載入 ---
def load_sounds():
    global background_sound, cover_sound # MODIFIED: Added cover_sound
    print("開始載入音效資源 (OGG)...")
    sound_files = {
        'player_shoot': 'ax01.ogg', 'boss_spawn': 'boss01.ogg', 'boss_defeat': 'boss02.ogg',
        'enemy_shoot': 'bg01.ogg', 'enemy_explosion': 'bg02.ogg', 'enemy_dive': 'bg03.ogg',
        'powerup': 'cz01.ogg', 'skill_activate': 'dx01.ogg', 'player_hit': 'ga01.ogg', # MODIFIED: pom_skill -> skill_activate
        'game_over': 'gg.ogg', 'ui_click': 'kc.ogg'
    }
    for key, filename in sound_files.items():
        path = os.path.join(SND_DIR, filename); sounds[key] = None
        if not os.path.exists(path): print(f"  警告：音效檔不存在 {filename} (預期為 .ogg)"); continue
        try:
            sound_obj = pygame.mixer.Sound(path)
            # Volume adjustments from original code
            if key == 'ui_click': sound_obj.set_volume(0.7)
            elif key == 'player_shoot': sound_obj.set_volume(0.5)
            elif key == 'enemy_explosion': sound_obj.set_volume(0.6)
            elif key == 'skill_activate': sound_obj.set_volume(0.7) # Assuming similar volume for skill
            sounds[key] = sound_obj
        except Exception as e: print(f"  錯誤：載入音效 {filename}: {e}"); sounds[key] = None

    # Load game background music
    game_music_file = 'background.ogg'
    _path_game_music = os.path.join(SND_DIR, game_music_file)
    if os.path.exists(_path_game_music):
        try:
            background_sound = pygame.mixer.Sound(_path_game_music)
            print(f"  遊戲背景音樂加載為 Sound 對象: {game_music_file}")
        except Exception as e:
             print(f"  錯誤：將遊戲背景音樂加載為 Sound 對象失敗 {game_music_file}: {e}")
             background_sound = None
    else:
        print(f"  警告：遊戲背景音樂檔不存在 {game_music_file} (預期為 .ogg)")
        background_sound = None

    # MODIFIED: Load cover music (dq.ogg)
    cover_music_file = 'dq.ogg'
    _path_cover_music = os.path.join(SND_DIR, cover_music_file)
    if os.path.exists(_path_cover_music):
        try:
            cover_sound = pygame.mixer.Sound(_path_cover_music)
            cover_sound.set_volume(0.6) # Example volume, adjust as needed
            print(f"  封面音樂加載為 Sound 對象: {cover_music_file}")
        except Exception as e:
            print(f"  錯誤：將封面音樂加載為 Sound 對象失敗 {cover_music_file}: {e}")
            cover_sound = None
    else:
        print(f"  警告：封面音樂檔不存在 {cover_music_file} (預期為 .ogg)")
        cover_sound = None

    print("音效資源載入完成.")

# --- 字體設定 ---
CUSTOM_FONT_FILENAME = "Cubic_11_1.000_R.ttf" # Keeping original font settings
def init_font():
    global main_font_path
    prospective_font_path = os.path.join(FONT_DIR, CUSTOM_FONT_FILENAME)
    if os.path.exists(prospective_font_path): main_font_path = prospective_font_path; print(f"使用自訂字體: {main_font_path}")
    else:
        print(f"警告：自訂字體文件 '{prospective_font_path}' 未找到！"); print("將嘗試使用 Pygame 預設字體 (可能無法顯示中文)。")
        main_font_path = pygame.font.get_default_font()
        if main_font_path: print(f"使用 Pygame 預設字體: {main_font_path}")
        else: print("警告：無法找到任何可用字型！文字可能無法顯示。"); main_font_path = None

def draw_text(surf, text, size, x, y, color=WHITE, align="midtop"):
    if not main_font_path: return
    try:
        font = pygame.font.Font(main_font_path, size); text_surface = font.render(text, True, color)
        align_dict = {align: (x, y)}; text_rect = text_surface.get_rect(**align_dict); surf.blit(text_surface, text_rect)
    except Exception as e:
        print(f"繪製文字 '{text}' (字體: {main_font_path}) 時發生錯誤: {e}")
        try:
            fallback_font = pygame.font.Font(None, size); text_surface = fallback_font.render(text, True, color)
            align_dict = {align: (x, y)}; text_rect = text_surface.get_rect(**align_dict); surf.blit(text_surface, text_rect)
        except Exception as e_fallback: print(f"備用字體繪製 '{text}' 也失敗: {e_fallback}")

def draw_ui(surf, level_disp, score_disp, lives_disp, skill_charges_disp, loop_count_disp): # MODIFIED: pom_charges_disp -> skill_charges_disp
    global fullscreen_button_rect
    ui_bar_height = 30; pygame.draw.rect(surf, BLACK, (0, 0, SCREEN_WIDTH, ui_bar_height))
    display_level_val = level_disp + loop_count_disp * MAX_LEVELS
    draw_text(surf, f"關卡:{display_level_val}", 18, 10, 5, align="topleft")
    draw_text(surf, f"分數:{score_disp}", 18, SCREEN_WIDTH / 2, 5, align="midtop")
    button_x = SCREEN_WIDTH - FULLSCREEN_BUTTON_SIZE[0] - FULLSCREEN_BUTTON_MARGIN
    button_y = (ui_bar_height - FULLSCREEN_BUTTON_SIZE[1]) // 2
    fullscreen_button_rect = pygame.Rect(button_x, button_y, FULLSCREEN_BUTTON_SIZE[0], FULLSCREEN_BUTTON_SIZE[1])
    pygame.draw.rect(surf, FULLSCREEN_BUTTON_COLOR, fullscreen_button_rect)
    button_text = "F" if not is_fullscreen else "W"
    draw_text(surf, button_text, 18, fullscreen_button_rect.centerx, fullscreen_button_rect.centery, FULLSCREEN_BUTTON_TEXT_COLOR, align="center")
    lives_text_width_estimate = 90; lives_x_pos = fullscreen_button_rect.left - lives_text_width_estimate - 10
    draw_text(surf, f"生命:{lives_disp}", 18, lives_x_pos, 5, align="topleft")

    # MODIFIED: UI for skill charges
    skill_icon_width_estimate = 80; skill_icon_x_pos = lives_x_pos - skill_icon_width_estimate - 10
    if assets.get('skill_icon'): # Using the renamed 'skill_icon' key
        try:
            icon = pygame.transform.scale(assets['skill_icon'], (25, 25)); surf.blit(icon, (skill_icon_x_pos, 5))
            draw_text(surf, f"x {skill_charges_disp}", 18, skill_icon_x_pos + 30, 8, align="topleft")
        except Exception as e: print(f"繪製技能圖示錯誤: {e}"); draw_text(surf, f"技能:{skill_charges_disp}", 18, skill_icon_x_pos, 5, align="topleft")
    else: draw_text(surf, f"技能:{skill_charges_disp}", 18, skill_icon_x_pos, 5, align="topleft")

def draw_health_bar(surf, x, y, pct, bar_length=100, bar_height=10, color_stages=True):
    pct = max(0, min(pct, 100)); fill_width = (pct / 100) * bar_length
    outline_rect = pygame.Rect(x, y, bar_length, bar_height); fill_rect = pygame.Rect(x, y, fill_width, bar_height)
    bar_color = RED;
    if color_stages: bar_color = GREEN if pct > 60 else YELLOW if pct > 30 else RED
    pygame.draw.rect(surf, bar_color, fill_rect); pygame.draw.rect(surf, WHITE, outline_rect, 2)

# --- Enemy and Level Data (Copied from v8.2.16, no change in structure) ---
enemy_data={'p01':{'hp':1,'score':10,'behavior':'normal_slow'},'p02':{'hp':1,'score':20,'behavior':'normal_fast'},'p03':{'hp':2,'score':30,'behavior':'shooter_single'},'p04':{'hp':2,'score':40,'behavior':'diver_curve'},'p05':{'hp':2,'score':50,'behavior':'shooter_burst'},'p06':{'hp':3,'score':60,'behavior':'diver_fast'},'p07':{'hp':3,'score':70,'behavior':'shooter_spread'},'p08':{'hp':3,'score':80,'behavior':'hybrid'},'p09':{'hp':3,'score':90,'behavior':'item'}}
level_data=[{'enemies':{'p01':8,'p02':2},'boss':None},{'enemies':{'p01':8,'p02':4,'p09':1},'boss':None},{'enemies':{'p01':10,'p02':4,'p09':1},'boss':None},{'enemies':{'p01':12,'p02':6,'p09':2},'boss':None},{'enemies':{'p01':10,'p02':6,'p03':2},'boss':None},{'enemies':{'p01':6,'p02':6,'p03':4,'p09':2},'boss':None},{'enemies':{'p01':4,'p02':8,'p03':4,'p09':2},'boss':None},{'enemies':{'p01':4,'p02':8,'p03':4,'p09':2},'boss':None},{'enemies':{'p01':4,'p02':8,'p03':6,'p09':2},'boss':None},{'enemies':{},'boss':'boss10'},{'enemies':{'p02':8,'p03':2},'boss':None},{'enemies':{'p02':8,'p03':4,'p09':1},'boss':None},{'enemies':{'p02':10,'p03':4,'p09':1},'boss':None},{'enemies':{'p02':12,'p03':6,'p09':2},'boss':None},{'enemies':{'p02':10,'p03':6,'p04':2},'boss':None},{'enemies':{'p02':6,'p03':6,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':6,'p09':2},'boss':None},{'enemies':{'p01':8,'p02':8,'p03':8},'boss':'boss20'},{'enemies':{'p02':8,'p03':2},'boss':None},{'enemies':{'p02':8,'p03':4,'p09':2},'boss':None},{'enemies':{'p02':10,'p03':4,'p09':2},'boss':None},{'enemies':{'p02':12,'p03':6,'p09':2},'boss':None},{'enemies':{'p02':10,'p03':6,'p04':2},'boss':None},{'enemies':{'p02':6,'p03':6,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':4,'p09':2},'boss':None},{'enemies':{'p02':4,'p03':8,'p04':6,'p09':2},'boss':None},{'enemies':{'p02':8,'p04':8,'p05':8},'boss':'boss30'},{'enemies':{'p02':4,'p03':6,'p04':4,'p09':2},'boss':None},{'enemies':{'p04':8,'p05':8,'p09':2},'boss':None},{'enemies':{'p05':12,'p06':6,'p09':2},'boss':None},{'enemies':{'p05':12,'p07':8,'p09':2},'boss':None},{'enemies':{'p06':12,'p07':10,'p03':2},'boss':None},{'enemies':{'p04':8,'p05':6,'p06':4,'p07':4,'p09':2},'boss':None},{'enemies':{'p04':8,'p05':8,'p06':6,'p07':4,'p09':2},'boss':None},{'enemies':{'p04':6,'p05':8,'p06':6,'p07':6,'p09':2},'boss':None},{'enemies':{'p04':6,'p05':8,'p06':8,'p07':6,'p09':2},'boss':None},{'enemies':{'p05':8,'p06':8,'p07':8},'boss':'boss40'},{'enemies':{'p03':4,'p06':6,'p07':4,'p09':2},'boss':None},{'enemies':{'p05':8,'p06':8,'p09':2},'boss':None},{'enemies':{'p07':12,'p08':6,'p09':2},'boss':None},{'enemies':{'p07':10,'p08':8,'p09':2},'boss':None},{'enemies':{'p07':12,'p08':10,'p03':2},'boss':None},{'enemies':{'p06':8,'p07':6,'p08':8,'p09':2},'boss':None},{'enemies':{'p07':14,'p08':12,'p09':2},'boss':None},{'enemies':{'p07':10,'p08':16,'p09':2},'boss':None},{'enemies':{'p08':28,'p09':2},'boss':None},{'enemies':{'p07':12,'p08':12},'boss':'boss50'}]
MAX_LEVELS = len(level_data)
FORMATION_COLS=10; FORMATION_ROWS=5; FORMATION_START_X=100; FORMATION_START_Y=60; FORMATION_SPACING_X=60; FORMATION_SPACING_Y=50

# --- Global Game State Variables ---
player = None; all_sprites = None; enemies = None; player_bullets = None; enemy_bullets = None; boss_group = None; powerups = None
game_state = ""; current_level = 0; score = 0; click_times = []; level_transition_timer = 0; loop_count = 0; difficulty_multiplier = 1.0

# --- Classes ---
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(); self.image_orig = assets.get('player') # Uses 'zg.png'
        if self.image_orig: self.image = self.image_orig.copy()
        else: print("警告:Player無圖"); self.image_orig = pygame.Surface([50,60]); self.image_orig.fill(GREEN); self.image = self.image_orig.copy()
        self.rect = self.image.get_rect()
        try: self.mask = pygame.mask.from_surface(self.image)
        except Exception as e: print(f"警告:Player mask創建失敗:{e}"); self.mask = None
        self.rect.centerx = SCREEN_WIDTH // 2; self.rect.bottom = SCREEN_HEIGHT - 10; self.lives = PLAYER_INITIAL_LIVES
        self.skill_charges = PLAYER_INITIAL_SKILL_CHARGES # MODIFIED: Renamed from pomeranian_charges
        self.score_for_next_life = PLAYER_SCORE_PER_LIFE
        self.current_score_progress = 0; self.shoot_delay = PLAYER_INITIAL_SHOOT_DELAY
        self.last_shot_time = pygame.time.get_ticks(); self.hidden = False; self.hide_timer = pygame.time.get_ticks()
        self.bullet_level_n = 0; self.bullet_level_w = 0
        self.max_bullet_level_n = 3; self.max_bullet_level_w = 5

    def update(self, dt):
        now = pygame.time.get_ticks()
        if self.hidden:
            if now - self.hide_timer > PLAYER_INVINCIBILITY_DURATION: self.hidden = False; self.image.set_alpha(255) if hasattr(self.image, 'set_alpha') else None
            elif hasattr(self.image, 'set_alpha'): self.image.set_alpha(255 if (now // 100) % 2 == 0 else 100)
        else:
            if hasattr(self.image, 'set_alpha'): self.image.set_alpha(255) # Ensure full alpha when not hidden
            mouse_x, _ = pygame.mouse.get_pos(); self.rect.centerx = mouse_x
            if self.rect.left < 0: self.rect.left = 0
            if self.rect.right > SCREEN_WIDTH: self.rect.right = SCREEN_WIDTH
            self.auto_shoot()

    def auto_shoot(self):
        global all_sprites, player_bullets; now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.shoot_delay:
            self.last_shot_time = now; num_bullets = self.bullet_level_n + 1; spread_pixels = self.bullet_level_w * 7
            start_x = self.rect.centerx - spread_pixels * (num_bullets - 1) / 2.0 if num_bullets > 1 else self.rect.centerx
            level_sum = self.bullet_level_n + self.bullet_level_w
            bullet_color = WHITE if level_sum <= 1 else CYAN if level_sum <= 3 else YELLOW if level_sum <= 6 else MAGENTA
            for i in range(num_bullets):
                bullet_x = max(2, min(SCREEN_WIDTH - 2, start_x + i * spread_pixels))
                bullet_y = self.rect.top - 15
                bullet = Bullet(bullet_x, bullet_y, c=bullet_color)
                if all_sprites is not None: all_sprites.add(bullet)
                if player_bullets is not None: player_bullets.add(bullet)
            if sounds.get('player_shoot'): sounds['player_shoot'].play()

    def hide(self):
        if not self.hidden: self.hidden = True; self.hide_timer = pygame.time.get_ticks(); print("玩家受傷, 暫時無敵!"); sounds['player_hit'].play() if sounds.get('player_hit') else None # MODIFIED: Player hit message
    def add_life(self): self.lives += 1; print(f"生命增加! 生命: {self.lives}")
    def add_skill_charge(self): self.skill_charges += 1; print(f"技能充能增加! 充能: {self.skill_charges}") # MODIFIED
    def check_score_for_life(self, gained_score):
        self.current_score_progress += gained_score
        if self.current_score_progress >= self.score_for_next_life:
            lives_to_add = self.current_score_progress // self.score_for_next_life; self.current_score_progress %= self.score_for_next_life
            for _ in range(lives_to_add): self.add_life()
    def apply_powerup(self, type_char):
        global score; print(f"玩家拾取強化道具: {type_char}"); sounds['powerup'].play() if sounds.get('powerup') else None
        if type_char == 'H': self.add_life()
        elif type_char == 'P': self.add_skill_charge() # MODIFIED: 'P' now adds skill charge
        elif type_char == 'S': self.shoot_delay = max(80, self.shoot_delay - 40); print(f"射速提升! 新延遲: {self.shoot_delay}")
        elif type_char == 'N':
             if self.bullet_level_n < self.max_bullet_level_n: self.bullet_level_n += 1; print(f"子彈數量等級提升至 {self.bullet_level_n+1}!")
             else: print("子彈數量已達上限!"); score += 50 if score is not None else 0
        elif type_char == 'W':
             if self.bullet_level_w < self.max_bullet_level_w: self.bullet_level_w += 1; print(f"子彈擴散等級提升至 {self.bullet_level_w}!")
             else: print("子彈擴散已達上限!"); score += 50 if score is not None else 0

class Bullet(pygame.sprite.Sprite): # Player bullet
    def __init__(self,x,y,s=-10 * FPS,c=WHITE,w=4,h=12): # s is speed in pixels per second
        super().__init__(); self.image=pygame.Surface([w,h]); self.image.fill(c)
        self.rect=self.image.get_rect(centerx=x, top=y)
        self.speedy_per_sec = s
    def update(self, dt): # dt is delta time in seconds
        self.rect.y += self.speedy_per_sec * dt;
        self.kill() if self.rect.bottom < 0 else None

class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, s=5 * FPS, speed_x=0 * FPS, color=RED, width=6, height=12):
        super().__init__(); self.image = pygame.Surface([width, height]); self.image.fill(color)
        self.rect = self.image.get_rect(centerx=x, top=y); self.speedy_per_sec = s; self.speedx_per_sec = speed_x
        try: self.mask = pygame.mask.from_surface(self.image)
        except Exception as e: self.mask = None; print(f"警告: EnemyBullet mask創建失敗: {e}")
    def update(self, dt):
        self.rect.x += self.speedx_per_sec * dt; self.rect.y += self.speedy_per_sec * dt
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.left > SCREEN_WIDTH or self.rect.right < 0: self.kill()

class SkillAnimation(pygame.sprite.Sprite): # MODIFIED: Renamed from Pomeranian to SkillAnimation
    def __init__(self, position_key="bottomleft"):
        super().__init__(); self.frames = []; f1 = assets.get('skill_anim1'); f2 = assets.get('skill_anim2') # Using renamed keys
        if f1: self.frames.append(f1)
        if f2: self.frames.append(f2)
        if not self.frames: f_icon = assets.get('skill_icon'); self.frames.append(f_icon) if f_icon else self.frames.append(pygame.Surface([30,30]).fill(ORANGE)) # Fallback
        self.current_frame = 0; self.image = self.frames[self.current_frame]; self.rect = self.image.get_rect()
        setattr(self.rect, position_key, (10, SCREEN_HEIGHT - 10) if position_key=="bottomleft" else (SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.spawn_time = pygame.time.get_ticks(); self.lifetime = 600; self.anim_delay = 150; self.last_anim_update = self.spawn_time
    def update(self, dt):
        now = pygame.time.get_ticks()
        if now - self.spawn_time > self.lifetime: self.kill(); return
        if len(self.frames) > 1 and (now - self.last_anim_update > self.anim_delay):
            self.last_anim_update = now; self.current_frame = (self.current_frame + 1) % len(self.frames)
            center = self.rect.center; self.image = self.frames[self.current_frame]; self.rect = self.image.get_rect(center=center)

class Enemy(pygame.sprite.Sprite): # (No changes needed in Enemy class logic for "套皮" if filenames are same)
    def __init__(self, enemy_id_str, formation_pos_tuple):
        super().__init__(); self.enemy_id = enemy_id_str; self.formation_pos = formation_pos_tuple
        self.image_orig = assets.get(enemy_id_str)
        if not self.image_orig: print(f"警告:Enemy {enemy_id_str} 無圖"); self.image_orig = pygame.Surface([40, 30]); self.image_orig.fill(RED); draw_text(self.image_orig, enemy_id_str, 12, 20, 15, WHITE, align="center")
        self.image = self.image_orig.copy(); self.rect = self.image.get_rect()
        try: self.mask = pygame.mask.from_surface(self.image)
        except Exception as e: print(f"警告:Enemy {enemy_id_str} mask創建失敗:{e}"); self.mask = None
        self.rect.centerx = random.randint(self.rect.width // 2, SCREEN_WIDTH - self.rect.width // 2); self.rect.bottom = random.randint(-150, -self.rect.height - 20)
        data = enemy_data.get(enemy_id_str, {'hp': 1, 'score': 10, 'behavior': 'normal_slow'}); base_hp = data['hp']; base_score_val = data['score']
        self.hp = max(1, round(base_hp * difficulty_multiplier)); self.max_hp = self.hp; self.score_value = round(base_score_val * (1.0 + loop_count * 0.2))
        self.behavior = data['behavior']; self.state = 'entering'
        self.enter_speed_pps = random.uniform(2.5 * FPS, 4.5 * FPS); self.dive_speed_pps = random.uniform(4 * FPS, 8 * FPS); self.return_speed_pps = 3 * FPS
        self.dive_path = None; self.dive_path_index = 0; self.last_action_time = pygame.time.get_ticks() + random.randint(800, 2000)
        self.action_delay = random.randint(3000, 6000); self.is_hit = False; self.hit_timer = 0
    def update(self, dt): # Logic remains the same
        now = pygame.time.get_ticks()
        if self.is_hit:
            hit_duration = 150
            if now - self.hit_timer < hit_duration: self.image.set_alpha(255 if (now // 50) % 2 == 0 else 100) if hasattr(self.image, 'set_alpha') else None
            else: self.is_hit = False; self.image = self.image_orig.copy(); self.image.set_alpha(255) if hasattr(self.image, 'set_alpha') else None
        if self.state == 'entering':
            target_x, target_y = self.formation_pos; dx = target_x - self.rect.centerx; dy = target_y - self.rect.centery; distance = math.hypot(dx, dy)
            move_dist_this_frame = self.enter_speed_pps * dt
            if distance < move_dist_this_frame * 1.1: self.rect.center = self.formation_pos; self.state = 'formation'; self.last_action_time = now + random.randint(500, 2000)
            else: move_x = (dx / distance) * move_dist_this_frame; move_y = (dy / distance) * move_dist_this_frame; self.rect.x += move_x; self.rect.y += move_y
        elif self.state == 'formation':
            idle_offset_x = math.sin(now / 700.0 + self.formation_pos[0] / 60.0) * 3; idle_offset_y = math.sin(now / 800.0 + self.formation_pos[1] / 70.0) * 2
            self.rect.centerx = self.formation_pos[0] + idle_offset_x; self.rect.centery = self.formation_pos[1] + idle_offset_y
            if now - self.last_action_time > self.action_delay: self.decide_action()
            else:
                can_shoot = self.behavior in ['shooter_single', 'shooter_burst', 'shooter_spread', 'hybrid']
                if can_shoot and random.random() < 0.002 : self.shoot(); self.last_action_time = now + random.randint(1500, 2500) # Reduced random shoot chance a bit
        elif self.state == 'diving':
            if self.dive_path and self.dive_path_index < len(self.dive_path):
                target_pos = self.dive_path[self.dive_path_index]; dx = target_pos[0] - self.rect.centerx; dy = target_pos[1] - self.rect.centery; distance = math.hypot(dx, dy)
                move_dist_this_frame = self.dive_speed_pps * dt
                if distance < move_dist_this_frame * 1.1:
                    self.dive_path_index += 1
                    if self.behavior in ['shooter_single', 'shooter_burst', 'shooter_spread', 'hybrid'] and random.random() < 0.35: self.shoot()
                else: move_x = (dx / distance) * move_dist_this_frame; move_y = (dy / distance) * move_dist_this_frame; self.rect.x += move_x; self.rect.y += move_y
                if self.dive_path_index >= len(self.dive_path): self.state = 'returning'; self.dive_path = None
            else: self.state = 'returning'; self.dive_path = None
            if self.rect.top > SCREEN_HEIGHT + 50 : self.state = 'returning'; self.dive_path = None # Ensure it returns if goes too far off screen
        elif self.state == 'returning':
            target_x, target_y = self.formation_pos; dx = target_x - self.rect.centerx; dy = target_y - self.rect.centery; distance = math.hypot(dx, dy)
            move_dist_this_frame = self.return_speed_pps * dt
            if distance < move_dist_this_frame * 1.1: self.rect.center = self.formation_pos; self.state = 'formation'; self.last_action_time = now + random.randint(1000, 3000)
            else: move_x = (dx / distance) * move_dist_this_frame; move_y = (dy / distance) * move_dist_this_frame; self.rect.x += move_x; self.rect.y += move_y
            if self.rect.bottom < -20 : self.rect.center = self.formation_pos; self.state = 'formation'; print(f"{self.enemy_id} Flew too high returning, reset.") # Failsafe
    def decide_action(self): # Logic remains the same
        self.last_action_time = pygame.time.get_ticks(); self.action_delay = random.randint(3000, 6000) # Reset action delay
        can_shoot = self.behavior in ['shooter_single', 'shooter_burst', 'shooter_spread', 'hybrid']; can_dive = self.behavior != 'item'; action_roll = random.random(); dive_chance = 0.30
        if self.behavior == 'diver_curve': dive_chance = 0.50
        elif self.behavior == 'diver_fast': dive_chance = 0.55
        elif self.behavior == 'hybrid': dive_chance = 0.45
        elif self.behavior == 'normal_fast': dive_chance = 0.35
        elif self.behavior == 'shooter_single': dive_chance = 0.25
        shoot_chance_after_dive_check = 0.6; global player
        if can_dive and action_roll < dive_chance and player and player.alive(): self.start_dive(player)
        elif can_shoot and random.random() < shoot_chance_after_dive_check: self.shoot()
    def start_dive(self, target_sprite): # Logic remains the same
        if self.state == 'formation' and target_sprite and target_sprite.alive():
            self.state = 'diving'; self.dive_path = self.generate_dive_path(target_sprite); self.dive_path_index = 0
            if self.behavior == 'diver_fast': self.dive_speed_pps = random.uniform(7 * FPS, 10 * FPS)
            elif self.behavior == 'diver_curve': self.dive_speed_pps = random.uniform(5 * FPS, 7 * FPS)
            else: self.dive_speed_pps = random.uniform(4 * FPS, 6 * FPS)
            if not self.dive_path: self.state = 'formation'; return
            if sounds.get('enemy_dive'): sounds['enemy_dive'].play()
    def generate_dive_path(self, target_sprite): # Logic remains the same
        path = []; start_pos = self.rect.center
        player_center = target_sprite.rect.center if target_sprite and target_sprite.alive() else (SCREEN_WIDTH/2, SCREEN_HEIGHT * 0.8)
        path_type = random.choice(['swoop', 'loop', 'straight_ish', 'cross_screen'])
        if self.behavior == 'diver_curve': path_type = random.choice(['swoop', 'loop', 'cross_screen'])
        elif self.behavior == 'diver_fast': path_type = random.choice(['straight_ish', 'swoop'])
        if path_type == 'swoop':
            p1_y = start_pos[1] + 150 + random.randint(-30, 30); p1_x_direction = 1 if start_pos[0] < SCREEN_WIDTH/2 else -1; p1_x = start_pos[0] + random.randint(-80, 80) * p1_x_direction; p1 = (max(50, min(SCREEN_WIDTH - 50, p1_x)), p1_y)
            p2_y = player_center[1] + random.randint(-40, 80); p2_x = player_center[0] + random.randint(-100, 100); p2 = (max(50, min(SCREEN_WIDTH - 50, p2_x)), max(p1_y + 50, p2_y))
            p3_y = SCREEN_HEIGHT * 0.6 + random.randint(-50, 50); p3_x = start_pos[0] + random.randint(-100, 100); p3 = (max(50, min(SCREEN_WIDTH - 50, p3_x)), min(max(start_pos[1] + 50, p1_y + 20), p2_y - 50, p3_y)); path.extend([p1, p2, p3])
        elif path_type == 'loop':
            p1_y = start_pos[1] + 100 + random.randint(0, 50); p1_x_direction = 1 if start_pos[0] < SCREEN_WIDTH/2 else -1; p1_x = start_pos[0] + random.randint(50, 100) * p1_x_direction; p1 = (max(30, min(SCREEN_WIDTH - 30, p1_x)), p1_y)
            p2_y = p1_y + random.randint(80, 150); p2_x = start_pos[0]; p2 = (max(30, min(SCREEN_WIDTH - 30, p2_x)), p2_y)
            p3_y = p1_y; p3_x_direction = -1 if start_pos[0] < SCREEN_WIDTH/2 else 1; p3_x = start_pos[0] + random.randint(50, 100) * p3_x_direction; p3 = (max(30, min(SCREEN_WIDTH - 30, p3_x)), p3_y); path.extend([p1, p2, p3])
        elif path_type == 'cross_screen':
            p1_y = start_pos[1] + 200 + random.randint(-20, 20); p1_x = start_pos[0] + random.randint(-50, 50); p1 = (max(50, min(SCREEN_WIDTH - 50, p1_x)), max(start_pos[1] + 100, p1_y))
            p2_y = p1_y + random.randint(-10, 10); p2_x = SCREEN_WIDTH - start_pos[0] + random.randint(-80, 80); p2 = (max(50, min(SCREEN_WIDTH - 50, p2_x)), p2_y); path.extend([p1, p2])
        else: p1_y = player_center[1] + random.randint(50, 150); p1_x = player_center[0] + random.randint(-80, 80); p1 = (max(50, min(SCREEN_WIDTH - 50, p1_x)), p1_y); path.append(p1)
        return path
    def shoot(self): # Logic remains the same
        global all_sprites, enemy_bullets;
        if self.state not in ['formation', 'diving']: return; sounds['enemy_shoot'].play() if sounds.get('enemy_shoot') else None
        if self.behavior == 'shooter_single' or (self.behavior == 'hybrid' and random.random() < 0.7): bullet = EnemyBullet(self.rect.centerx, self.rect.bottom + 5, color=RED); all_sprites.add(bullet); enemy_bullets.add(bullet)
        elif self.behavior == 'shooter_burst':
            for i in range(3): bullet = EnemyBullet(self.rect.centerx + random.randint(-3, 3), self.rect.bottom + 5 + i*10, s=7*FPS, color=ORANGE); all_sprites.add(bullet); enemy_bullets.add(bullet)
            self.action_delay += 500
        elif self.behavior == 'shooter_spread':
            num_bullets = 3; spread_angle = math.pi / 5; bullet_speed_pps = 6 * FPS
            for i in range(num_bullets):
                angle = -spread_angle/2 + (i*spread_angle/(num_bullets-1)) if num_bullets>1 else 0
                b_speed_x_pps = bullet_speed_pps * math.sin(angle); b_speed_y_pps = bullet_speed_pps * math.cos(angle)
                bullet = EnemyBullet(self.rect.centerx, self.rect.bottom+5, s=b_speed_y_pps, speed_x=b_speed_x_pps, color=CYAN); all_sprites.add(bullet); enemy_bullets.add(bullet)
            self.action_delay += 800
        elif self.behavior == 'hybrid' and random.random() < 0.4:
            num_bullets = 3; spread_angle = math.pi / 6; bullet_speed_pps = 5 * FPS
            for i in range(num_bullets):
                angle = -spread_angle/2 + (i*spread_angle/(num_bullets-1)) if num_bullets>1 else 0
                b_speed_x_pps = bullet_speed_pps * math.sin(angle); b_speed_y_pps = bullet_speed_pps * math.cos(angle)
                bullet = EnemyBullet(self.rect.centerx, self.rect.bottom+5, s=b_speed_y_pps, speed_x=b_speed_x_pps, color=PURPLE); all_sprites.add(bullet); enemy_bullets.add(bullet)
            self.action_delay += 600
        self.last_action_time = pygame.time.get_ticks()
    def take_damage(self, amount): # Logic remains the same
        if self.is_hit: return
        self.hp -= amount; self.is_hit = True; self.hit_timer = pygame.time.get_ticks()
        if self.hp <= 0: self.kill_enemy()
    def kill_enemy(self): # Logic remains the same
        global score, player;
        if not self.alive(): return; sounds['enemy_explosion'].play() if sounds.get('enemy_explosion') else None
        if player and score is not None: score += self.score_value; player.check_score_for_life(self.score_value)
        if self.enemy_id == 'p09': spawn_powerup(self.rect.center) # p09 is the item dropper
        self.kill()

class Boss(pygame.sprite.Sprite): # (No changes needed in Boss class logic for "套皮" if filenames are same)
    def __init__(self, boss_id_str):
        super().__init__(); self.boss_id = boss_id_str; self.image_orig = assets.get(boss_id_str)
        if not self.image_orig: print(f"警告: Boss {boss_id_str} 無圖"); self.image_orig=pygame.Surface([150,100]); self.image_orig.fill(PURPLE); draw_text(self.image_orig,boss_id_str,18,75,50,WHITE,align="center")
        self.image = self.image_orig.copy(); self.rect = self.image.get_rect()
        try: self.mask = pygame.mask.from_surface(self.image)
        except Exception as e: print(f"警告: Boss {boss_id_str} mask創建失敗:{e}"); self.mask = None
        self.rect.centerx=SCREEN_WIDTH/2; self.rect.top=-self.rect.height-20; boss_level_num = int(boss_id_str[-2:]); hp_map={ 10: 30, 20: 60, 30: 90, 40: 120, 50: 150 }; base_hp = hp_map.get(boss_level_num, 50)
        self.max_hp = max(10, round(base_hp * difficulty_multiplier)); self.hp = self.max_hp; self.score_value = round(1000 * (boss_level_num // 10) * (1.0 + loop_count * 0.2)); self.state='entering'
        self.speedx_pps=3.5 * FPS; self.speedy_pps=1.5 * FPS; self.shot_delay=1800; self.entry_target_y=80; self.first_attack_delay=800
        self.can_attack=False; self.last_shot_time=pygame.time.get_ticks(); self.num_bullets_spread = 9; self.is_hit = False; self.hit_timer = 0
        self.summon_timer = pygame.time.get_ticks(); self.summon_delay = 10000
    def update(self, dt): # Logic remains the same
        now=pygame.time.get_ticks()
        if self.is_hit:
            hit_duration = 100
            if now - self.hit_timer < hit_duration: self.image.set_alpha(255 if (now // 40) % 2 == 0 else 100) if hasattr(self.image, 'set_alpha') else None
            else: self.is_hit = False; self.image = self.image_orig.copy(); self.image.set_alpha(255) if hasattr(self.image, 'set_alpha') else None
        if self.state=='entering':
            self.rect.y += self.speedy_pps * dt
            if self.rect.top >= self.entry_target_y:
                self.rect.top = self.entry_target_y; print(f"Boss {self.boss_id} reached active pos. State: active"); self.state = 'active'; self.speedy_pps = 0
                self.can_attack = True; self.last_shot_time = now + self.first_attack_delay; self.summon_timer = now
                sounds['boss_spawn'].play() if sounds.get('boss_spawn') else None
        elif self.state=='active':
            self.rect.x += self.speedx_pps * dt
            if self.rect.left < 10 or self.rect.right > SCREEN_WIDTH - 10: self.speedx_pps *= -1
            if self.can_attack and (now - self.last_shot_time > self.shot_delay): self.shoot(); self.last_shot_time = now
            boss_level_num = int(self.boss_id[-2:])
            if boss_level_num >= 20 and now - self.summon_timer > self.summon_delay: self.summon_minions(boss_level_num); self.summon_timer = now
    def shoot(self): # Logic remains the same
        global all_sprites, enemy_bullets; sounds['enemy_shoot'].play() if sounds.get('enemy_shoot') else None
        spread_angle = math.pi * (2/3); bullet_speed_pps = 5.5 * FPS; center_angle = math.pi / 2
        start_angle = center_angle - spread_angle / 2 if self.num_bullets_spread > 1 else center_angle
        for i in range(self.num_bullets_spread):
            angle = start_angle + (i * spread_angle / (self.num_bullets_spread - 1)) if self.num_bullets_spread > 1 else start_angle
            b_speed_x_pps = bullet_speed_pps * math.cos(angle); b_speed_y_pps = bullet_speed_pps * math.sin(angle)
            if abs(b_speed_y_pps) <= bullet_speed_pps * 0.1 : b_speed_y_pps = bullet_speed_pps * 0.8 ; b_speed_x_pps = 0 # Prevent horizontal-only bullets, ensure some downward movement
            bullet = EnemyBullet(self.rect.centerx, self.rect.centery + self.rect.height / 3, s=b_speed_y_pps, speed_x=b_speed_x_pps, color=MAGENTA, width=8, height=16)
            all_sprites.add(bullet); enemy_bullets.add(bullet)
    def summon_minions(self, boss_level_num): # Logic remains the same
        global all_sprites, enemies; print(f"Boss {self.boss_id} summons minions!")
        summon_list = {20: {'p01': 4, 'p02': 4, 'p03': 2}, 30: {'p02': 4, 'p04': 4, 'p05': 2}, 40: {'p05': 4, 'p06': 4, 'p07': 2}, 50: {'p07': 6, 'p08': 6}}.get(boss_level_num, {})
        if not summon_list: print("  No summon list defined."); return
        max_enemies = FORMATION_COLS * FORMATION_ROWS
        for enemy_id, count in summon_list.items():
            for _ in range(count):
                if len(enemies) >= max_enemies * 0.8: print("  Too many enemies, skipping summon."); continue # Limit total enemies
                current_count = len(enemies); row = current_count // FORMATION_COLS; col = current_count % FORMATION_COLS; row = min(row, FORMATION_ROWS - 1); col = min(col, FORMATION_COLS - 1) # Simple placement
                pos_x = FORMATION_START_X + col * FORMATION_SPACING_X + random.randint(-5, 5); pos_y = FORMATION_START_Y + row * FORMATION_SPACING_Y + random.randint(-5, 5)
                formation_target = (max(30, min(SCREEN_WIDTH - 30, pos_x)), max(30, min(SCREEN_HEIGHT - 150, pos_y)))
                # Check if position is occupied and find new one if so (simple horizontal scan)
                is_occ = any(e.formation_pos == formation_target for e in enemies if hasattr(e, 'formation_pos'))
                if is_occ:
                    for _attempt in range(FORMATION_COLS): # Try to find an empty slot in the current row or nearby
                        temp_col = (_attempt + col) % FORMATION_COLS
                        new_pos_x = FORMATION_START_X + temp_col * FORMATION_SPACING_X; new_pos_y = FORMATION_START_Y + row * FORMATION_SPACING_Y
                        candidate_target = (max(30, min(SCREEN_WIDTH - 30, new_pos_x)), max(30, min(SCREEN_HEIGHT - 150, new_pos_y)))
                        if not any(e.formation_pos == candidate_target for e in enemies if hasattr(e, 'formation_pos')): formation_target = candidate_target; break
                minion = Enemy(enemy_id, formation_target)
                minion.rect.centerx = self.rect.centerx + random.randint(-self.rect.width//3, self.rect.width//3); minion.rect.bottom = self.rect.bottom + random.randint(10, 30); minion.state = 'entering'
                all_sprites.add(minion); enemies.add(minion)
    def take_damage(self, amount): # Logic remains the same
        if self.state == 'entering': print(f"Boss {self.boss_id} in 'entering' state, no damage taken."); return
        if self.is_hit: return
        self.hp -= amount; self.is_hit = True; self.hit_timer = pygame.time.get_ticks()
        if self.hp <= 0: self.kill_boss()
    def kill_boss(self): # Logic remains the same
        global score, player, enemies, enemy_bullets;
        if not self.alive(): return; print(f"Boss {self.boss_id} defeated!"); sounds['boss_defeat'].play() if sounds.get('boss_defeat') else None
        if player and score is not None: score += self.score_value; player.check_score_for_life(self.score_value);
        for enemy in enemies: enemy.kill() # Clear remaining minions
        for bullet in enemy_bullets: bullet.kill() # Clear boss bullets
        self.kill()

class PowerUp(pygame.sprite.Sprite): # (No changes needed in PowerUp class logic for "套皮" if filenames are same)
    def __init__(self, center_pos):
        super().__init__(); self.type = random.choice(['S', 'N', 'W', 'H', 'P']); self.image = pygame.Surface((30, 30), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (15, 15), 14); pygame.draw.circle(self.image, ORANGE, (15, 15), 14, 2)
        if main_font_path:
             try: font = pygame.font.Font(main_font_path, 20); text_surf = font.render(self.type, True, BLACK); text_rect = text_surf.get_rect(center=(15, 15)); self.image.blit(text_surf, text_rect)
             except Exception as e: print(f"繪製道具字母 '{self.type}' 使用自訂字體錯誤: {e}"); self.render_fallback_text()
        else: print("警告: PowerUp 字體無法設定 (main_font_path is None)"); pygame.draw.rect(self.image, RED, (5, 5, 20, 20)) # Fallback if no font at all
        self.rect = self.image.get_rect(center=center_pos); self.speedy_pps = 2.5 * FPS
    def render_fallback_text(self): # Fallback if custom font fails
         try: font = pygame.font.Font(None, 20); text_surf = font.render(self.type, True, BLACK); text_rect = text_surf.get_rect(center=(15,15)); self.image.blit(text_surf, text_rect)
         except Exception as e: print(f"備用字體繪製道具字母 '{self.type}' 也失敗: {e}"); pygame.draw.rect(self.image, RED, (5, 5, 20, 20)) # Ultimate fallback
    def update(self, dt): self.rect.y += self.speedy_pps * dt; self.kill() if self.rect.top > SCREEN_HEIGHT else None

# --- Game Functions ---
def spawn_wave(level_num_to_spawn): # (No changes needed in spawn_wave logic for "套皮" if filenames are same)
    global difficulty_multiplier, loop_count, MAX_LEVELS, all_sprites, enemies, enemy_bullets, powerups, boss_group
    print(f"開始生成關卡 {level_num_to_spawn + loop_count * MAX_LEVELS} (基礎 {level_num_to_spawn}, 循環 {loop_count}, 難度倍率 {difficulty_multiplier:.2f})...")
    if level_num_to_spawn < 1 or level_num_to_spawn > MAX_LEVELS: print(f"錯誤:無效基礎關卡{level_num_to_spawn}"); return
    # Clear previous wave entities except player and skill animations
    for sprite in all_sprites:
        if not isinstance(sprite, Player) and not isinstance(sprite, SkillAnimation): # MODIFIED
            sprite.kill()
    enemies.empty(); enemy_bullets.empty(); powerups.empty(); boss_group.empty()
    level_index = level_num_to_spawn - 1; data = level_data[level_index]; enemy_count = 0
    for enemy_id, count_num in data['enemies'].items():
        for _ in range(count_num):
            row = enemy_count // FORMATION_COLS; col = enemy_count % FORMATION_COLS
            # Try to find an empty spot if default is full (simple overflow handling)
            if row >= FORMATION_ROWS:
                found_pos = False
                for r_try in range(max(0, FORMATION_ROWS - 2), FORMATION_ROWS): # Try last few rows
                    for c_try in range(FORMATION_COLS):
                        temp_pos_check = (FORMATION_START_X + c_try * FORMATION_SPACING_X, FORMATION_START_Y + r_try * FORMATION_SPACING_Y)
                        is_occupied = any(e.formation_pos == temp_pos_check for e in enemies if hasattr(e, 'formation_pos'))
                        if not is_occupied: row, col = r_try, c_try; found_pos = True; break
                    if found_pos: break
                if not found_pos: continue # Skip spawning if no space found after trying
            pos_x = FORMATION_START_X + col * FORMATION_SPACING_X + random.randint(-5, 5); pos_y = FORMATION_START_Y + row * FORMATION_SPACING_Y + random.randint(-5, 5)
            formation_target = (max(30, min(SCREEN_WIDTH - 30, pos_x)), max(30, min(SCREEN_HEIGHT - 150, pos_y)))
            enemy = Enemy(enemy_id, formation_target); all_sprites.add(enemy); enemies.add(enemy); enemy_count += 1
    boss_id = data.get('boss')
    if boss_id and not boss_group.sprite: print(f"  生成 Boss: {boss_id}"); boss_obj = Boss(boss_id); all_sprites.add(boss_obj); boss_group.add(boss_obj); print(f"  Boss {boss_id} 已加入 all_sprites 和 boss_group. boss_group.sprite: {boss_group.sprite}")

def spawn_powerup(center_pos): powerup = PowerUp(center_pos); all_sprites.add(powerup); powerups.add(powerup)

# --- Main Game Function (Async) ---
async def main():
    global screen, clock, player, all_sprites, enemies, player_bullets, enemy_bullets, boss_group, powerups
    global game_state, current_level, score, click_times, level_transition_timer, loop_count, difficulty_multiplier
    global is_fullscreen, fullscreen_button_rect, background_sound, cover_sound, main_font_path # MODIFIED: Added cover_sound

    pygame.mixer.pre_init(44100, -16, 2, 512); pygame.init(); pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)); pygame.display.set_caption(GAME_TITLE); clock = pygame.time.Clock()
    init_font(); load_assets(); load_sounds()

    all_sprites = pygame.sprite.Group(); enemies = pygame.sprite.Group(); player_bullets = pygame.sprite.Group()
    enemy_bullets = pygame.sprite.Group(); boss_group = pygame.sprite.GroupSingle(); powerups = pygame.sprite.Group()
    game_state = "START_MENU"; current_level = 0; score = 0; player = None; click_times = []
    level_transition_timer = 0; LEVEL_TRANSITION_DELAY = 2000; loop_count = 0; difficulty_multiplier = 1.0
    continue_button_rect_local = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 50, 300, 50)
    menu_button_rect_local = pygame.Rect(SCREEN_WIDTH / 2 - 150, SCREEN_HEIGHT / 2 + 120, 300, 50)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        if dt == 0: dt = 1.0 / FPS # Prevent dt being zero if FPS is very high or tick returns 0
        if dt > (1.0 / FPS) * 3: dt = (1.0 / FPS) * 3 # Cap dt to prevent large jumps

        now_ticks = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: # Left click
                if fullscreen_button_rect and fullscreen_button_rect.collidepoint(event.pos):
                    is_fullscreen = not is_fullscreen; screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN if is_fullscreen else 0)
                    sounds['ui_click'].play() if sounds.get('ui_click') else None; print(f"Toggled fullscreen. Is fullscreen: {is_fullscreen}"); continue

            if game_state == "START_MENU":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    start_button_rect = pygame.Rect(SCREEN_WIDTH/2 - 100, SCREEN_HEIGHT*0.75, 200, 50)
                    if start_button_rect.collidepoint(event.pos):
                        if sounds.get('ui_click'): sounds['ui_click'].play()
                        # MODIFIED: Stop cover sound, start game background sound
                        if cover_sound: cover_sound.stop()
                        if background_sound:
                            try:
                                background_sound.stop() # Stop if already playing from a previous game over
                                background_sound.play(loops=-1)
                                print("遊戲背景音樂已開始.")
                            except Exception as e:
                                print(f"錯誤：播放遊戲背景 Sound 對象失敗: {e}")
                        else:
                            print("background_sound is None, cannot play BGM.")

                        current_level = 1; score = 0; loop_count = 0; difficulty_multiplier = 1.0
                        all_sprites.empty(); enemies.empty(); player_bullets.empty(); enemy_bullets.empty(); boss_group.empty(); powerups.empty()
                        player = Player(); all_sprites.add(player); spawn_wave(current_level); game_state = "PLAYING"; click_times = []

            elif game_state == "PLAYING":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                     now_time_sec = time.time(); click_times.append(now_time_sec); click_times = [t for t in click_times if now_time_sec - t < TRIPLE_CLICK_INTERVAL]
                     if len(click_times) >= 3:
                         if player and player.skill_charges > 0: # MODIFIED: pomeranian_charges -> skill_charges
                             print(f"發動強力攻擊! 造成 {SKILL_DAMAGE} 點傷害!"); # MODIFIED
                             sounds['skill_activate'].play() if sounds.get('skill_activate') else None # MODIFIED: pom_skill -> skill_activate
                             player.skill_charges -= 1; click_times = [] # MODIFIED
                             for es in enemies: es.take_damage(SKILL_DAMAGE) if hasattr(es, 'take_damage') else None # MODIFIED: POMERANIAN_DAMAGE -> SKILL_DAMAGE
                             if boss_group.sprite and hasattr(boss_group.sprite, 'take_damage'): boss_group.sprite.take_damage(SKILL_DAMAGE) # MODIFIED
                             all_sprites.add(SkillAnimation(position_key="bottomleft")); all_sprites.add(SkillAnimation(position_key="bottomright")) # MODIFIED: Pomeranian -> SkillAnimation
                         elif player: print("技能能量不足!"); click_times = [] # MODIFIED

            elif game_state == "POST_VICTORY_CHOICE":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if continue_button_rect_local.collidepoint(event.pos):
                        if sounds.get('ui_click'): sounds['ui_click'].play()
                        # MODIFIED: Stop cover (if somehow playing), start game BGM
                        if cover_sound: cover_sound.stop()
                        if background_sound:
                            try:
                                background_sound.stop()
                                background_sound.play(loops=-1)
                                print("遊戲背景音樂已開始 (Post Victory).")
                            except Exception as e:
                                print(f"錯誤：播放遊戲背景 Sound 對象失敗 (Post Victory): {e}")
                        else:
                            print("background_sound is None (Post Victory), cannot play BGM.")

                        difficulty_multiplier = 1.0 + loop_count * 0.15; print(f"新難度倍率: {difficulty_multiplier:.2f}"); current_level = 1
                        player_bullets.empty(); enemy_bullets.empty(); powerups.empty(); boss_group.empty(); [se.kill() for se in enemies]
                        spawn_wave(current_level); game_state = "PLAYING"
                    elif menu_button_rect_local.collidepoint(event.pos):
                        if sounds.get('ui_click'): sounds['ui_click'].play()
                        if background_sound: background_sound.stop()
                        # MODIFIED: Cover sound will be started by START_MENU state logic
                        loop_count = 0; difficulty_multiplier = 1.0; game_state = "START_MENU"

            elif game_state == "GAME_OVER":
                 if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                     if sounds.get('ui_click'): sounds['ui_click'].play()
                     if background_sound: background_sound.stop()
                     # MODIFIED: Cover sound will be started by START_MENU state logic
                     loop_count = 0; difficulty_multiplier = 1.0; game_state = "START_MENU"

        # --- Game State Updates ---
        if game_state == "START_MENU":
            # MODIFIED: Play cover sound if not already playing
            if cover_sound and not pygame.mixer.Channel(0).get_sound() == cover_sound : # A bit more robust check
                # Check if any channel is playing cover_sound. This is tricky with Sound objects directly.
                # A simpler check is if it was *meant* to be playing.
                # Let's assume if we are in START_MENU, it should be playing.
                # If game_music or other sounds are playing, this might conflict.
                # For now, a simple play if not busy (assuming cover_sound has its own logic or dedicated channel if needed)
                try:
                    # Stop other main sounds first
                    if background_sound and background_sound.get_num_channels() > 0: background_sound.stop()
                    # Play cover sound if not already playing on some channel
                    # This check is imperfect for Sound objects. Ideally, use a specific channel.
                    # For simplicity, we'll just try to play it. If it's already playing, play() might restart or do nothing.
                    if not any(pygame.mixer.Channel(i).get_sound() == cover_sound for i in range(pygame.mixer.get_num_channels())):
                         cover_sound.play(loops=-1)
                         print("封面音樂已開始.")
                except Exception as e:
                    print(f"錯誤：播放封面 Sound 對象失敗: {e}")


        elif game_state == "PLAYING":
            all_sprites.update(dt)
            if player and player.alive():
                hit_enemies_dict = pygame.sprite.groupcollide(enemies, player_bullets, False, True, pygame.sprite.collide_mask)
                for enemy_hit, bullets_that_hit in hit_enemies_dict.items():
                    if hasattr(enemy_hit, 'take_damage'):
                        for _ in bullets_that_hit: enemy_hit.take_damage(1) # Assuming 1 damage per bullet
                if boss_group.sprite and boss_group.sprite.alive():
                    the_boss = boss_group.sprite; coll_func_boss = pygame.sprite.collide_mask if (hasattr(the_boss, 'mask') and the_boss.mask) else pygame.sprite.collide_rect
                    boss_hits = pygame.sprite.groupcollide(boss_group, player_bullets, False, True, collided=coll_func_boss)
                    if boss_hits:
                        for actual_boss, bullets_hit in boss_hits.items():
                            if hasattr(actual_boss, 'take_damage'):
                                for _ in bullets_hit: actual_boss.take_damage(1) # Assuming 1 damage per bullet
                if not player.hidden:
                    p_coll_func = pygame.sprite.collide_mask if player.mask else pygame.sprite.collide_rect
                    if pygame.sprite.spritecollide(player, enemy_bullets, True, p_coll_func): player.lives -= 1; player.hide()
                    if player.lives > 0 and not player.hidden: # Check again after bullet collision
                        # Check collision with diving enemies
                        if any(p_coll_func(player, enemy_obj) and hasattr(enemy_obj, 'state') and enemy_obj.state == 'diving' for enemy_obj in enemies): player.lives -= 1; player.hide()
                    if player.lives > 0 and not player.hidden and boss_group.sprite and boss_group.sprite.alive(): # Check again
                        if p_coll_func(player, boss_group.sprite): player.lives -= 1; player.hide()
                    if player.lives <= 0:
                        print("玩家生命耗盡! 遊戲結束.")
                        if background_sound: background_sound.stop()
                        if cover_sound: cover_sound.stop() # MODIFIED: Stop cover sound on game over
                        sounds['game_over'].play() if sounds.get('game_over') else None
                        player.kill(); game_state = "GAME_OVER"
                for p_up in pygame.sprite.spritecollide(player, powerups, True, pygame.sprite.collide_circle_ratio(0.7)): player.apply_powerup(p_up.type) if hasattr(player, 'apply_powerup') else None
            if player and player.alive() and game_state == "PLAYING": # Check if all enemies/boss defeated
                is_boss_lvl = bool(level_data[current_level - 1]['boss']) if 0 < current_level <= MAX_LEVELS else False; boss_dead = not boss_group.sprite
                if (not is_boss_lvl and not enemies) or (is_boss_lvl and boss_dead and not enemies): # Ensure regular enemies also cleared on boss levels if any spawn after boss
                     lvl_disp = current_level + loop_count * MAX_LEVELS; print(f"關卡 {lvl_disp} 完成!")
                     [b.kill() for b in enemy_bullets]; [p.kill() for p in powerups]; [e.kill() for e in enemies] if not is_boss_lvl else None # Clear non-boss enemies too
                     next_lvl = current_level + 1
                     if next_lvl > MAX_LEVELS:
                         print("最高基礎關卡完成...")
                         if background_sound: background_sound.stop()
                         if cover_sound: cover_sound.stop() # MODIFIED
                         loop_count += 1; game_state = "POST_VICTORY_CHOICE"
                     else: game_state = "LEVEL_TRANSITION"; level_transition_timer = now_ticks
        elif game_state == "LEVEL_TRANSITION":
            if now_ticks - level_transition_timer > LEVEL_TRANSITION_DELAY:
                current_level += 1; print(f"開始載入關卡 {current_level + loop_count * MAX_LEVELS}..."); player_bullets.empty(); spawn_wave(current_level); game_state = "PLAYING"

        # --- Drawing ---
        screen.fill(BLACK)
        if game_state == "START_MENU":
            screen.blit(assets['cover'], (0, 0)) if assets.get('cover') else draw_text(screen, GAME_TITLE, 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.15, align="center")
            start_btn = pygame.Rect(SCREEN_WIDTH / 2 - 100, SCREEN_HEIGHT * 0.75, 200, 50); pygame.draw.rect(screen, RED, start_btn, border_radius=10); draw_text(screen, "開始遊戲", 24, start_btn.centerx, start_btn.centery, WHITE, align="center"); draw_text(screen, "滑鼠移動 | 左鍵三連擊發動技能", 16, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.90, WHITE, align="center")
        elif game_state == "PLAYING":
            all_sprites.draw(screen); draw_ui(screen, current_level, score, player.lives, player.skill_charges, loop_count) if player and player.alive() else None # MODIFIED
            if boss_group.sprite and hasattr(boss_group.sprite, 'hp') and hasattr(boss_group.sprite, 'max_hp') and boss_group.sprite.max_hp > 0: draw_health_bar(screen, SCREEN_WIDTH / 2 - 150, 35, (boss_group.sprite.hp / boss_group.sprite.max_hp) * 100, bar_length=300, bar_height=15)
        elif game_state == "LEVEL_TRANSITION":
            all_sprites.draw(screen); draw_ui(screen, current_level, score, player.lives, player.skill_charges, loop_count) if player and player.alive() else None # MODIFIED
            lvl_disp = current_level + loop_count * MAX_LEVELS; draw_text(screen, f"關卡 {lvl_disp} 完成！", 54, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 40, YELLOW, align="center")
            next_lvl_disp = current_level + 1 + loop_count * MAX_LEVELS; draw_text(screen, f"準備進入第 {next_lvl_disp} 關...", 28, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 40, WHITE, align="center") if current_level + 1 <= MAX_LEVELS else None
        elif game_state == "POST_VICTORY_CHOICE":
            draw_text(screen, f"第 {loop_count} 輪通關！", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, GREEN, align="center"); draw_text(screen, f"總分數: {score}", 36, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 20, WHITE, align="center")
            pygame.draw.rect(screen, GREEN, continue_button_rect_local, border_radius=10); draw_text(screen, f"繼續遊戲 (關卡 {1 + loop_count * MAX_LEVELS})", 24, continue_button_rect_local.centerx, continue_button_rect_local.centery, BLACK, align="center")
            pygame.draw.rect(screen, RED, menu_button_rect_local, border_radius=10); draw_text(screen, "返回主選單", 24, menu_button_rect_local.centerx, menu_button_rect_local.centery, WHITE, align="center")
            tmp_l = player.lives if player and hasattr(player, 'lives') else 0; tmp_c = player.skill_charges if player and hasattr(player, 'skill_charges') else 0; draw_ui(screen, current_level, score, tmp_l, tmp_c, loop_count) # MODIFIED
        elif game_state == "GAME_OVER":
            draw_text(screen, "GAME OVER", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, RED, align="center"); draw_text(screen, f"最終分數: {score}", 36, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE, align="center"); draw_text(screen, "按下滑鼠左鍵返回主選單", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75, WHITE, align="center"); draw_ui(screen, current_level, score, 0, 0, loop_count) # MODIFIED: skill_charges to 0
        elif game_state == "WIN_SCREEN": # This state seems unused in original flow, but kept for completeness
            draw_text(screen, "戰鬥仍將繼續！", 64, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4, GREEN, align="center"); draw_text(screen, f"最終分數: {score}", 36, SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, WHITE, align="center"); draw_text(screen, "按下滑鼠左鍵重新開始", 22, SCREEN_WIDTH / 2, SCREEN_HEIGHT * 0.75, WHITE, align="center")
            tmp_l = player.lives if player and hasattr(player, 'lives') else 0; tmp_c = player.skill_charges if player and hasattr(player, 'skill_charges') else 0; draw_ui(screen, current_level, score, tmp_l, tmp_c, loop_count) # MODIFIED

        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == '__main__':
    try: asyncio.run(main())
    except RuntimeError as e:
        if "Event loop is closed" in str(e) or "Cannot run nested event loops" in str(e): print("Asyncio loop issue detected.") # Common in some environments
        else: raise e