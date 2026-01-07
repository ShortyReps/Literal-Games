import dearpygui.dearpygui as dpg
import requests, re, json, threading, time, os, sys, webbrowser, glob, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from pypresence import Presence
from tkinter import Tk, filedialog
from io import BytesIO
try:
    import psutil
except ImportError:
    psutil = None
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

APP_NAME = "Buttstrap Pro"
VERSION = "Release 1.3"
CLIENT_ID = "1455620291920265432"
DISCORD_LINK = "https://discord.gg/cRDH3D2jKn"

TABS = {
    "h": "HOME", 
    "q": "QUESTS",
    "mv": "ENGINE & MODS",
    "l": "LOGS", 
    "s": "GEAR", 
    "a": "ABOUT"
}

POPULAR_GAMES = {
    "Adopt Me!": {"place_id": "920587237", "name": "Adopt Me!"},
    "Brookhaven RP": {"place_id": "4924922222", "name": "Brookhaven RP"},
    "Blox Fruits": {"place_id": "2753915549", "name": "Blox Fruits"},
    "Pet Simulator X": {"place_id": "6284583030", "name": "Pet Simulator X"},
    "Arsenal": {"place_id": "286090429", "name": "Arsenal"},
    "Doors": {"place_id": "6516141723", "name": "Doors"},
    "Tower of Hell": {"place_id": "1962086868", "name": "Tower of Hell"},
    "Jailbreak": {"place_id": "606849621", "name": "Jailbreak"},
    "Welcome to Bloxburg": {"place_id": "185655149", "name": "Welcome to Bloxburg"},
    "Royale High": {"place_id": "735030788", "name": "Royale High"}
}

THEMES = {
    "Modern Dark": {"bg": (15, 15, 15), "child": (24, 24, 24), "btn": (35, 35, 35), "text": (240, 240, 240), "acc": (0, 180, 255), "cost": 0, "unlocked": True},
    "Modern Light": {"bg": (245, 245, 245), "child": (255, 255, 255), "btn": (230, 230, 230), "text": (30, 30, 30), "acc": (0, 120, 200), "cost": 0, "unlocked": True},
    "Midnight Blue": {"bg": (10, 10, 18), "child": (15, 15, 25), "btn": (25, 25, 40), "text": (200, 210, 255), "acc": (65, 105, 225), "cost": 50, "unlocked": False},
    "Crimson Night": {"bg": (20, 10, 10), "child": (30, 15, 15), "btn": (45, 20, 20), "text": (255, 230, 230), "acc": (220, 20, 60), "cost": 75, "unlocked": False},
    "Vaporwave": {"bg": (30, 10, 40), "child": (45, 15, 60), "btn": (60, 20, 80), "text": (0, 255, 255), "acc": (255, 0, 255), "cost": 100, "unlocked": False},
    "Femboy Pink": {"bg": (255, 240, 245), "child": (255, 255, 255), "btn": (255, 220, 235), "text": (80, 80, 90), "acc": (255, 105, 180), "cost": 150, "unlocked": False},
    "Neon Green": {"bg": (10, 25, 10), "child": (15, 35, 15), "btn": (20, 50, 20), "text": (150, 255, 150), "acc": (0, 255, 100), "cost": 125, "unlocked": False},
    "Ocean Blue": {"bg": (5, 15, 25), "child": (10, 25, 35), "btn": (15, 35, 50), "text": (180, 220, 255), "acc": (0, 150, 255), "cost": 80, "unlocked": False}
}

PRESETS = {
    "Competitive (Max FPS)": {"FFlagRenderCheckThreading": "True", "DFIntTaskSchedulerTargetFps": "9999", "FFlagFasterPreciseTime4": "True"},
    "Visual Ultra (Quality)": {"FIntDebugForceMSAASamples": "4", "DFFlagDisableDPIScale": "True", "FFlagDebugGraphicsPreferVulkan": "True"},
    "Potato PC Mode": {"FIntRenderShadowIntensity": "0", "FFlagVisualEngineD3D11DisableShadows": "True", "FIntTerrainArraySliceSize": "4"}
}

class Buttstrapper:
    def __init__(self):
        self.app_dir = Path(os.path.expanduser("~")) / ".ButtstrapPro"
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.icons_dir = self.app_dir / "icons"
        self.icons_dir.mkdir(exist_ok=True)
        defaults = {
            "theme": "Modern Dark", "flags": {}, "fps": "999", "rpc_enabled": True, 
            "path": "", "render_api": "Vulkan", "no_shadows": False, "msaa": "0",
            "topbar_off": False, "old_textures": False, "priority": "High",
            "live_inject_unlocked": False, "vr_mode": False, "fullscreen": True,
            "games": [], "gems": 0, "unlocked_themes": ["Modern Dark", "Modern Light"],
            "quests": {}, "roblox_start_time": None, "current_game_place_id": None
        }
        self.config = self.load_json("config.json", defaults)
        self.rpc = None
        self.roblox_path = ""
        self.roblox_process = None
        self.status_detail = ""
        self.animation_alpha = {}
        self.quest_completions = []
        self.current_tab = "h"
        self.engine_subtab = "visual"
        self.button_animations = {}
        self.image_registry = {}
        self.show_quests_in_home = False
        threading.Thread(target=self.service_init, daemon=True).start()
        threading.Thread(target=self.monitor_roblox, daemon=True).start()
        threading.Thread(target=self.quest_tracker, daemon=True).start()
        threading.Thread(target=self.animation_loop, daemon=True).start()

    def load_json(self, name, default):
        p = self.app_dir / name
        try: return {**default, **json.loads(p.read_text())} if p.exists() else default
        except: return default

    def save_config(self):
        with open(self.app_dir / "config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def create_pixel_art_icon(self, name, place_id):
        """Create a pixel art icon for the game"""
        try:
            icon_path = self.icons_dir / f"{place_id}_pixel.png"
            
            # If already exists, return it
            if icon_path.exists():
                return str(icon_path)
            
            if PIL_AVAILABLE:
                img = Image.new('RGB', (150, 150), color=(50, 50, 70))
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                # Draw a colorful pixel art game icon
                # Background gradient effect
                for y in range(150):
                    color_val = int(50 + (y / 150) * 30)
                    draw.line([(0, y), (150, y)], fill=(color_val, color_val, color_val + 20))
                
                # Draw game controller shape
                draw.rectangle([25, 35, 125, 115], fill=(100, 150, 255), outline=(200, 200, 255), width=2)
                # Buttons
                draw.ellipse([40, 50, 60, 70], fill=(255, 255, 255))
                draw.ellipse([90, 50, 110, 70], fill=(255, 255, 255))
                # D-pad
                draw.rectangle([55, 85, 75, 105], fill=(255, 255, 255))
                # Game name initial letter
                if name:
                    try:
                        from PIL import ImageFont
                        # Try to use default font
                        font = ImageFont.load_default()
                        initial = name[0].upper()
                        bbox = draw.textbbox((0, 0), initial, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        draw.text((75 - text_width//2, 60 - text_height//2), initial, fill=(100, 150, 255), font=font)
                    except:
                        pass
                
                img.save(icon_path)
                return str(icon_path)
            else:
                # Create a simple colored square if PIL not available
                import struct
                pixels = []
                for y in range(150):
                    for x in range(150):
                        r = 50 + (x // 10) % 50
                        g = 50 + (y // 10) % 50
                        b = 70 + ((x + y) // 10) % 50
                        pixels.append(struct.pack('BBB', r, g, b))
                with open(icon_path, 'wb') as f:
                    # Write as simple PPM format
                    f.write(b'P6\n150 150\n255\n')
                    f.write(b''.join(pixels))
                return str(icon_path)
        except Exception as e:
            print(f"Error creating pixel art: {e}")
            return None

    def load_pixel_art_icon(self, icon_path, place_id):
        """Load pixel art icon and register it with DearPyGUI"""
        if not icon_path or not os.path.exists(icon_path):
            return None
        try:
            texture_tag = f"tex_{place_id}_pixel"
            
            # Check if already registered
            if texture_tag in self.image_registry:
                if dpg.does_item_exist(texture_tag):
                    return texture_tag
            
            # Load the pixel art image
            try:
                width, height, channels, data = dpg.load_image(icon_path)
                # Ensure texture registry exists
                if not dpg.does_item_exist("texture_registry"):
                    with dpg.texture_registry(show=False, tag="texture_registry"):
                        pass
                with dpg.texture_registry(show=False):
                    dpg.add_static_texture(width, height, data, tag=texture_tag)
                self.image_registry[texture_tag] = texture_tag
                return texture_tag
            except Exception as e:
                print(f"Error loading pixel art: {e}")
                return None
        except Exception:
            pass
        return None

    def update_status_detail(self, text):
        self.status_detail = text
        if dpg.does_item_exist("status_detail"):
            dpg.set_value("status_detail", text)
            dpg.configure_item("status_detail", color=(200, 200, 200, 255))

    def set_status(self, text, color=(0, 180, 255)):
        if dpg.does_item_exist("status_text"):
            dpg.set_value("status_text", f"STATUS: {text.upper()}")
            dpg.configure_item("status_text", color=color)
            self.update_status_detail(text)

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        if dpg.does_item_exist("log_box"):
            dpg.add_text(f"[{ts}] [{level}] {msg}", parent="log_box")
            dpg.set_y_scroll("log_box", -1.0)

    def animate_button_click(self, button_tag):
        """Animate button click with pulse effect"""
        if dpg.does_item_exist(button_tag):
            original_color = dpg.get_item_configuration(button_tag).get("color", (100, 100, 100))
            # Pulse animation
            for i in range(3):
                def pulse(alpha):
                    if dpg.does_item_exist(button_tag):
                        pulse_color = tuple(int(c * (0.7 + 0.3 * alpha)) for c in original_color[:3])
                        dpg.configure_item(button_tag, color=pulse_color)
                threading.Timer(i * 0.1, lambda a=i/3: pulse(a)).start()

    def switch_tab(self, tab_key):
        """Switch tabs with fade animation"""
        if self.current_tab == tab_key:
            return
        
        # Fade out current tab
        if dpg.does_item_exist(f"tc_{self.current_tab}"):
            dpg.configure_item(f"tc_{self.current_tab}", show=False)
        
        # Fade in new tab
        self.current_tab = tab_key
        if dpg.does_item_exist(f"tc_{tab_key}"):
            dpg.configure_item(f"tc_{tab_key}", show=True)

    def service_init(self):
        self.roblox_path = self.find_roblox()
        if self.config.get("rpc_enabled"): self.update_rpc()

    def update_rpc(self):
        try:
            if self.config.get("rpc_enabled"):
                if not self.rpc:
                    self.rpc = Presence(CLIENT_ID)
                    self.rpc.connect()
                self.rpc.update(state="Engine Active", details=f"Buttstrap {VERSION}", start=time.time())
            elif self.rpc:
                self.rpc.close(); self.rpc = None
        except: self.rpc = None

    def find_roblox(self):
        base_paths = [os.path.expandvars(r"%LocalAppData%\Roblox\Versions\*"), os.path.expandvars(r"%LocalAppData%\Bloxstrap\Versions\*")]
        for p in base_paths:
            vers = sorted(glob.glob(p), key=os.path.getmtime, reverse=True)
            for v in vers:
                if os.path.exists(os.path.join(v, "RobloxPlayerBeta.exe")): return os.path.realpath(v)
        return self.config.get("path", "")


    def launch_game(self, place_id=None, game_name="Roblox"):
        if not place_id:
            return self.launch()
        
        self.roblox_path = self.find_roblox()
        if not self.roblox_path:
            dpg.configure_item("setup_modal", show=True); return

        self.set_status("Applying ClientSettings...", (255, 200, 0))
        self.update_status_detail(f"Writing settings to {self.roblox_path}\\ClientSettings")
        cs_dir = os.path.join(self.roblox_path, "ClientSettings")
        os.makedirs(cs_dir, exist_ok=True)
        
        injection = {**self.config["flags"], "DFIntTaskSchedulerTargetFps": self.config["fps"]}
        if self.config["no_shadows"]: injection["FIntRenderShadowIntensity"] = "0"
        if self.config["topbar_off"]: injection["FFlagEnableInGameMenuControls"] = "False"
        if self.config["render_api"] == "Vulkan": injection["FFlagDebugGraphicsPreferVulkan"] = "True"
        
        try:
            settings_file = os.path.join(cs_dir, "ClientAppSettings.json")
            with open(settings_file, "w") as f:
                json.dump(injection, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            
            self.set_status("Launching game...", (0, 255, 150))
            self.update_status_detail(f"Opening {game_name} (Place ID: {place_id})")
            self.log(f"Launching game: {game_name} (Place ID: {place_id})")
            
            webbrowser.open(f"roblox://placeId={place_id}")
            
            self.config["current_game_place_id"] = place_id
            self.config["roblox_start_time"] = time.time()
            self.save_config()
            
            threading.Timer(5, lambda: self.set_status("IDLE", (150, 150, 150))).start()
        except Exception as e:
            self.set_status("LAUNCH ERROR", (255, 50, 50))
            self.update_status_detail(f"Error: {str(e)}")
            self.log(f"Fail: {e}", "ERROR")

    def launch(self, place_id=None):
        self.roblox_path = self.find_roblox()
        if not self.roblox_path:
            dpg.configure_item("setup_modal", show=True); return

        self.set_status("Applying ClientSettings...", (255, 200, 0))
        self.update_status_detail(f"Writing settings to {self.roblox_path}\\ClientSettings")
        cs_dir = os.path.join(self.roblox_path, "ClientSettings")
        os.makedirs(cs_dir, exist_ok=True)
        
        injection = {**self.config["flags"], "DFIntTaskSchedulerTargetFps": self.config["fps"]}
        if self.config["no_shadows"]: injection["FIntRenderShadowIntensity"] = "0"
        if self.config["topbar_off"]: injection["FFlagEnableInGameMenuControls"] = "False"
        if self.config["render_api"] == "Vulkan": injection["FFlagDebugGraphicsPreferVulkan"] = "True"
        
        try:
            settings_file = os.path.join(cs_dir, "ClientAppSettings.json")
            self.update_status_detail(f"Writing ClientAppSettings.json...")
            with open(settings_file, "w") as f:
                json.dump(injection, f, indent=4)
                f.flush()
                os.fsync(f.fileno())
            
            self.set_status("Injecting Live FFLAGS...", (0, 255, 150))
            self.update_status_detail(f"Injected {len(injection)} flags")
            self.log(f"Injected {len(injection)} flags into {settings_file}")
            
            time.sleep(0.1)
            
            self.set_status("Opening Roblox...", (0, 180, 255))
            self.update_status_detail("Starting RobloxPlayerBeta.exe")
            cmd = [os.path.join(self.roblox_path, "RobloxPlayerBeta.exe"), "--app"]
            if self.config["fullscreen"]: cmd.append("-fullscreen")
            
            self.roblox_process = subprocess.Popen(cmd)
            self.config["roblox_start_time"] = time.time()
            self.save_config()
            threading.Timer(5, lambda: self.set_status("IDLE", (150, 150, 150))).start()
        except Exception as e:
            self.set_status("LAUNCH ERROR", (255, 50, 50))
            self.update_status_detail(f"Error: {str(e)}")
            self.log(f"Fail: {e}", "ERROR")

    def monitor_roblox(self):
        while True:
            try:
                time.sleep(2)
                if self.config.get("roblox_start_time"):
                    roblox_running = False
                    if psutil:
                        for proc in psutil.process_iter(['pid', 'name']):
                            try:
                                if 'roblox' in proc.info['name'].lower():
                                    roblox_running = True
                                    break
                            except: pass
                    else:
                        if self.roblox_process:
                            roblox_running = (self.roblox_process.poll() is None)
                    
                    if not roblox_running and self.config.get("roblox_start_time"):
                        self.check_quest_completions()
                        self.config["roblox_start_time"] = None
                        self.config["current_game_place_id"] = None
                        self.save_config()
            except: pass

    def check_quest_completions(self):
        completed = []
        play_time = 0
        if self.config.get("roblox_start_time"):
            play_time = int((time.time() - self.config["roblox_start_time"]) / 60)
        
        if not self.config.get("quests", {}).get("open_roblox", False):
            self.config.setdefault("quests", {})["open_roblox"] = True
            self.add_gems(10)
            completed.append({"name": "Open Roblox", "reward": 10})
        
        if play_time >= 5 and not self.config.get("quests", {}).get("play_5min", False):
            self.config.setdefault("quests", {})["play_5min"] = True
            self.add_gems(15)
            completed.append({"name": "Play for 5 minutes", "reward": 15})
        
        if play_time >= 15 and not self.config.get("quests", {}).get("play_15min", False):
            self.config.setdefault("quests", {})["play_15min"] = True
            self.add_gems(25)
            completed.append({"name": "Play for 15 minutes", "reward": 25})
        
        if play_time >= 30 and not self.config.get("quests", {}).get("play_30min", False):
            self.config.setdefault("quests", {})["play_30min"] = True
            self.add_gems(50)
            completed.append({"name": "Play for 30 minutes", "reward": 50})
        
        place_id = self.config.get("current_game_place_id")
        if place_id:
            quest_key = f"play_game_{place_id}"
            if not self.config.get("quests", {}).get(quest_key, False):
                self.config.setdefault("quests", {})[quest_key] = True
                self.add_gems(20)
                completed.append({"name": f"Play game (ID: {place_id})", "reward": 20})
        
        if completed:
            self.quest_completions = completed
            self.show_quest_completion_animation()
        
        self.save_config()

    def quest_tracker(self):
        while True:
            try:
                time.sleep(10)
                if self.config.get("roblox_start_time"):
                    play_time = int((time.time() - self.config["roblox_start_time"]) / 60)
                    if dpg.does_item_exist("quest_time"):
                        dpg.set_value("quest_time", f"Playing: {play_time} minutes")
            except: pass

    def add_gems(self, amount):
        self.config["gems"] = self.config.get("gems", 0) + amount
        self.save_config()
        if dpg.does_item_exist("gems_display"):
            dpg.set_value("gems_display", f"GEMS: {self.config['gems']}")
        if dpg.does_item_exist("gems_display_gear"):
            dpg.set_value("gems_display_gear", f"GEMS: {self.config['gems']}")

    def show_quest_completion_animation(self):
        if not self.quest_completions:
            return
        
        dpg.configure_item("quest_modal", show=True)
        dpg.delete_item("quest_list", children_only=True)
        
        for quest in self.quest_completions:
            with dpg.group(parent="quest_list", horizontal=True):
                dpg.add_text(f"✓ {quest['name']}", color=(0, 255, 100))
                dpg.add_spacer(width=20)
                dpg.add_text(f"+{quest['reward']} GEMS", color=(255, 215, 0))
        
        threading.Timer(5, lambda: dpg.configure_item("quest_modal", show=False)).start()

    def animation_loop(self):
        while True:
            try:
                time.sleep(0.016)
            except: pass

    def unlock_live_fflags(self):
        def confirm():
            self.config["live_inject_unlocked"] = True
            self.save_config()
            dpg.configure_item("exploit_warn_modal", show=False)
            self.log("RESTART REQUIRED TO ACCESS FFLAGS", "WARN")
        dpg.configure_item("exploit_warn_modal", show=True)
        dpg.set_item_callback("confirm_unlock_btn", confirm)

    def apply_theme(self, name):
        if name not in self.config.get("unlocked_themes", []):
            cost = THEMES[name].get("cost", 0)
            if self.config.get("gems", 0) < cost:
                self.set_status("INSUFFICIENT GEMS", (255, 50, 50))
                self.update_status_detail(f"Need {cost} GEMS to unlock {name}")
                return
            self.add_gems(-cost)
            self.config.setdefault("unlocked_themes", []).append(name)
            self.save_config()
        
        c = THEMES.get(name, THEMES["Modern Dark"])
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, c["bg"])
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, c["child"])
                dpg.add_theme_color(dpg.mvThemeCol_Button, c["btn"])
                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, c["acc"])
                dpg.add_theme_color(dpg.mvThemeCol_Text, c["text"])
        dpg.bind_theme(global_theme)
        self.config["theme"] = name
        self.save_config()
        self.update_theme_ui()

    def update_theme_ui(self):
        if dpg.does_item_exist("theme_list"):
            dpg.delete_item("theme_list", children_only=True)
            for name, theme in THEMES.items():
                unlocked = name in self.config.get("unlocked_themes", [])
                cost_text = f" ({theme['cost']} GEMS)" if not unlocked and theme['cost'] > 0 else ""
                btn_label = f"{name}{cost_text}"
                def make_callback(theme_name):
                    return lambda s, a: self.apply_theme(theme_name)
                dpg.add_button(label=btn_label, parent="theme_list", width=-1, 
                             callback=make_callback(name))

    def add_game_to_grid(self, place_id, name, icon_path=None):
        if not place_id or not name:
            self.set_status("INVALID INPUT", (255, 50, 50))
            self.update_status_detail("Place ID and Game Name are required")
            return
        
        # Always create pixel art icon
        self.update_status_detail(f"Creating pixel art icon for {name}...")
        icon_path = self.create_pixel_art_icon(name, place_id)
        
        game_data = {"place_id": place_id, "name": name, "icon": icon_path}
        self.config.setdefault("games", []).append(game_data)
        self.save_config()
        
        # Refresh grid immediately
        try:
            self.refresh_game_grid()
        except Exception as e:
            print(f"Error refreshing grid: {e}")
        
        if dpg.does_item_exist("new_place_id"):
            dpg.set_value("new_place_id", "")
        if dpg.does_item_exist("new_game_name"):
            dpg.set_value("new_game_name", "")
        
        self.set_status("GAME ADDED", (0, 255, 100))
        self.update_status_detail(f"Added {name} to gaming grid")

    def refresh_game_grid(self):
        try:
            if not dpg.does_item_exist("game_grid"):
                return
            
            dpg.delete_item("game_grid", children_only=True)
            games = self.config.get("games", [])
            
            # Horizontal scrollable grid - show up to 10 slots (5 empty by default)
            max_slots = 10
            # Always show at least 5 slots, show all games up to 10 slots maximum
            total_slots = max(5, min(len(games), max_slots))
            
            for idx in range(total_slots):
                if idx < len(games):
                    # Game slot
                    game = games[idx]
                    btn_tag = f"game_btn_{idx}"
                    
                    def make_launch_callback(place_id, name, btn_tag):
                        def callback(s, a):
                            self.animate_button_click(btn_tag)
                            self.launch_game(place_id, name)
                        return callback
                    
                    def make_remove_callback(game_idx, btn_tag):
                        def callback(s, a):
                            self.animate_button_click(btn_tag)
                            self.remove_game(game_idx)
                        return callback
                    
                    with dpg.child_window(width=100, height=135, border=True, parent="game_grid"):
                        # Load pixel art icon
                        icon_texture = None
                        if game.get("icon") and os.path.exists(game["icon"]):
                            icon_texture = self.load_pixel_art_icon(game["icon"], game["place_id"])
                        
                        if icon_texture and dpg.does_item_exist(icon_texture):
                            dpg.add_image(icon_texture, width=80, height=80)
                        else:
                            # Fallback: button with game name
                            with dpg.theme() as btn_theme:
                                with dpg.theme_component(dpg.mvButton):
                                    dpg.add_theme_color(dpg.mvThemeCol_Button, (50, 50, 70))
                                    dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (70, 70, 90))
                            dpg.push_theme_stack(btn_theme)
                            dpg.add_button(label=game.get("name", f"Game {idx+1}")[:12], 
                                         width=80, height=80, tag=btn_tag,
                                         callback=make_launch_callback(game["place_id"], game.get("name"), btn_tag))
                            dpg.pop_theme_stack()
                        
                        dpg.add_text(game.get("name", f"Game {idx+1}")[:18], wrap=120)
                        dpg.add_button(label="Remove", width=80, height=25,
                                     callback=make_remove_callback(idx, btn_tag))
                else:
                    # Empty slot
                    with dpg.child_window(width=100, height=135, border=True, parent="game_grid"):
                        with dpg.theme() as btn_theme:
                            with dpg.theme_component(dpg.mvButton):
                                dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 40))
                                dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (50, 50, 60))
                        dpg.push_theme_stack(btn_theme)
                        dpg.add_button(label="+", width=80, height=80, callback=lambda: dpg.configure_item("add_game_modal", show=True))
                        dpg.pop_theme_stack()
                        dpg.add_text("Empty Slot", wrap=120)
        except Exception as e:
            try:
                if dpg.does_item_exist("log_box"):
                    self.log(f"Error in refresh_game_grid: {e}", "ERROR")
                else:
                    print(f"Error in refresh_game_grid: {e}")
            except:
                print(f"Error in refresh_game_grid: {e}")

    def remove_game(self, index):
        games = self.config.get("games", [])
        if 0 <= index < len(games):
            games.pop(index)
            self.config["games"] = games
            self.save_config()
            # Refresh grid immediately (no delay needed)
            try:
                self.refresh_game_grid()
            except Exception as e:
                self.log(f"Error refreshing grid: {e}", "ERROR")

    def run(self):
        dpg.create_context()
        # Create texture registry early
        with dpg.texture_registry(show=False, tag="texture_registry"):
            pass
        
        with dpg.window(tag="main", no_title_bar=True, no_move=True, no_resize=True):
            with dpg.group(horizontal=True):
                dpg.add_button(label="LAUNCH ENGINE", width=180, height=45, callback=self.launch)
                dpg.add_spacer(width=5)
                for k, v in TABS.items():
                    if k != "q":  # Quests handled separately
                        label = v
                        def make_tab_callback(tab_key):
                            def callback(s, a):
                                self.animate_button_click(f"tab_{tab_key}")
                                self.switch_tab(tab_key)
                            return callback
                        dpg.add_button(label=label, width=105, height=45, tag=f"tab_{k}",
                                     callback=make_tab_callback(k))

            dpg.add_separator()
            with dpg.child_window(height=480, border=False):
                # HOME TAB - Unified with gaming grid
                with dpg.group(tag="tc_h"):
                    with dpg.group(horizontal=True):
                        with dpg.child_window(width=300, height=200, border=True):
                            dpg.add_text("System Info", color=(255, 200, 0))
                            dpg.add_text(f"Library: {len(self.config['flags'])} Flags")
                            dpg.add_text(f"Live Inject: {'ENABLED' if self.config['live_inject_unlocked'] else 'LOCKED'}")
                            dpg.add_text(f"GEMS: {self.config.get('gems', 0)}", tag="gems_display", color=(255, 215, 0))
                            dpg.add_button(label="View Quests", width=-1, height=30,
                                         callback=lambda: self.switch_tab("q"))
                        
                        with dpg.child_window(width=300, height=200, border=True):
                            dpg.add_text("Quick Presets", color=(255, 200, 0))
                            for n in PRESETS.keys():
                                def make_preset_callback(preset_name):
                                    def callback(s, a):
                                        self.config["flags"].update(PRESETS[preset_name])
                                        self.save_config()
                                        self.set_status("PRESET APPLIED", (0, 255, 100))
                                    return callback
                                dpg.add_button(label=n, width=-1, callback=make_preset_callback(n))
                    
                    dpg.add_separator()
                    dpg.add_text("GAMING GRID", color=(0, 180, 255))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="+ Add Game", width=120, height=40,
                                     callback=lambda: dpg.configure_item("add_game_modal", show=True))
                        dpg.add_button(label="Popular Games", width=120, height=40,
                                     callback=lambda: dpg.configure_item("popular_games_modal", show=True))
                    
                    # Horizontal scrollable grid
                    with dpg.child_window(width=-1, height=300, border=True, tag="game_grid_container", horizontal_scrollbar=True):
                        with dpg.group(tag="game_grid", horizontal=True):
                            pass

                # QUESTS TAB
                with dpg.group(tag="tc_q", show=False):
                    dpg.add_text("QUESTS", color=(0, 180, 255))
                    dpg.add_text("Active Quests:", color=(255, 200, 0))
                    dpg.add_text("• Open Roblox - 10 GEMS", color=(0, 255, 100) if self.config.get("quests", {}).get("open_roblox") else (200, 200, 200))
                    dpg.add_text("• Play for 5 minutes - 15 GEMS", color=(0, 255, 100) if self.config.get("quests", {}).get("play_5min") else (200, 200, 200))
                    dpg.add_text("• Play for 15 minutes - 25 GEMS", color=(0, 255, 100) if self.config.get("quests", {}).get("play_15min") else (200, 200, 200))
                    dpg.add_text("• Play for 30 minutes - 50 GEMS", color=(0, 255, 100) if self.config.get("quests", {}).get("play_30min") else (200, 200, 200))
                    dpg.add_text("• Play any game - 20 GEMS", color=(200, 200, 200))
                    dpg.add_separator()
                    dpg.add_text("Current Session", color=(255, 200, 0))
                    dpg.add_text("Not playing", tag="quest_time", color=(150, 150, 150))
                    dpg.add_button(label="Back to Home", width=200, height=40,
                                 callback=lambda: self.switch_tab("h"))

                # ENGINE & MODS TAB - Now with sub-tabs
                with dpg.group(tag="tc_mv", show=False):
                    dpg.add_text("ENGINE & MODS", color=(0, 180, 255))
                    with dpg.group(horizontal=True):
                        dpg.add_button(label="Visual", width=100, height=30,
                                     callback=lambda: [dpg.configure_item("sub_visual", show=True),
                                                      dpg.configure_item("sub_launch", show=False),
                                                      dpg.configure_item("sub_fflags", show=False)])
                        dpg.add_button(label="Launch", width=100, height=30,
                                     callback=lambda: [dpg.configure_item("sub_visual", show=False),
                                                      dpg.configure_item("sub_launch", show=True),
                                                      dpg.configure_item("sub_fflags", show=False)])
                        dpg.add_button(label="FFLAGS", width=100, height=30,
                                     callback=lambda: [dpg.configure_item("sub_visual", show=False),
                                                      dpg.configure_item("sub_launch", show=False),
                                                      dpg.configure_item("sub_fflags", show=True)])
                    
                    with dpg.group(tag="sub_visual"):
                        dpg.add_text("VISUAL OVERRIDES", color=(0, 180, 255))
                        dpg.add_combo(["Vulkan", "D3D11", "D3D10", "OpenGL"], label="Rendering API", default_value=self.config["render_api"], callback=lambda s,a: self.config.update({"render_api": a}))
                        dpg.add_slider_int(label="MSAA Level", min_value=0, max_value=8, default_value=int(self.config["msaa"]), callback=lambda s,a: self.config.update({"msaa": str(a)}))
                        dpg.add_checkbox(label="Disable Global Shadows", default_value=self.config["no_shadows"], callback=lambda s,a: self.config.update({"no_shadows": a}))
                        dpg.add_text("CLIENT MODS", color=(0, 180, 255))
                        dpg.add_checkbox(label="Hide In-Game Topbar", default_value=self.config["topbar_off"], callback=lambda s,a: self.config.update({"topbar_off": a}))
                        dpg.add_checkbox(label="Enable Legacy Textures", default_value=self.config["old_textures"], callback=lambda s,a: self.config.update({"old_textures": a}))
                    
                    with dpg.group(tag="sub_launch", show=False):
                        dpg.add_text("LAUNCH CONFIGURATION", color=(0, 180, 255))
                        dpg.add_input_text(label="Global FPS Cap", default_value=self.config["fps"], callback=lambda s,a: self.config.update({"fps": a}))
                        dpg.add_combo(["High", "Normal", "Low"], label="Process Priority", default_value=self.config["priority"], callback=lambda s,a: self.config.update({"priority": a}))
                        dpg.add_checkbox(label="Enable VR Mode", default_value=self.config["vr_mode"], callback=lambda s,a: self.config.update({"vr_mode": a}))
                        dpg.add_checkbox(label="Force Fullscreen", default_value=self.config["fullscreen"], callback=lambda s,a: self.config.update({"fullscreen": a}))
                    
                    with dpg.group(tag="sub_fflags", show=False):
                        if self.config["live_inject_unlocked"]:
                            dpg.add_input_text(multiline=True, width=-1, height=400, tag="flag_editor", default_value=json.dumps(self.config["flags"], indent=4))
                            dpg.add_button(label="APPLY MANUAL CHANGES", width=-1, height=40, callback=lambda: self.config.update({"flags": json.loads(dpg.get_value("flag_editor"))}))
                        else:
                            dpg.add_spacer(height=150)
                            dpg.add_text("FFLAG LIVE INJECTING IS CURRENTLY DISABLED", color=(255, 50, 50), indent=250)

                with dpg.group(tag="tc_l", show=False): dpg.add_child_window(tag="log_box", height=-1)

                with dpg.group(tag="tc_s", show=False):
                    dpg.add_text("THEMES", color=(0, 180, 255))
                    dpg.add_text(f"GEMS: {self.config.get('gems', 0)}", tag="gems_display_gear", color=(255, 215, 0))
                    with dpg.group(tag="theme_list"):
                        pass
                    dpg.add_separator()
                    dpg.add_checkbox(label="Discord Rich Presence", default_value=self.config["rpc_enabled"], callback=lambda s,a: [self.config.update({"rpc_enabled": a}), self.update_rpc()])
                    dpg.add_checkbox(label="Unlock Live FFlag Injecting", default_value=self.config["live_inject_unlocked"], callback=self.unlock_live_fflags)
                    dpg.add_button(label="LOCATE ROBLOX", width=-1, callback=lambda: self.config.update({"path": filedialog.askdirectory()}))

                with dpg.group(tag="tc_a", show=False):
                    dpg.add_text("DEVELOPERS:", color=(255, 100, 150))
                    dpg.add_text("- Kemoflyx\n- Prookiewahs")
                    dpg.add_button(label="Join Official Discord", width=200, callback=lambda: webbrowser.open(DISCORD_LINK))

            dpg.add_separator()
            with dpg.group(horizontal=True):
                dpg.add_text("STATUS: IDLE", tag="status_text", color=(150, 150, 150))
                dpg.add_spacer(width=10)
                dpg.add_text("", tag="status_detail", color=(200, 200, 200))
                dpg.add_spacer(width=300)
                dpg.add_text(f"Buttstrap {VERSION}", color=(100, 100, 100))

        # Modals
        with dpg.window(label="CRITICAL WARNING", modal=True, show=False, tag="exploit_warn_modal", width=500, height=200):
            dpg.add_text("Live FFlag injection can be detected as third-party manipulation.")
            dpg.add_text("RESTART REQUIRED after enabling.")
            with dpg.group(horizontal=True):
                dpg.add_button(label="ACCEPT RISK", tag="confirm_unlock_btn", width=200)
                dpg.add_button(label="CANCEL", width=200, callback=lambda: dpg.configure_item("exploit_warn_modal", show=False))

        with dpg.window(label="Quest Completed!", modal=True, show=False, tag="quest_modal", width=400, height=300):
            dpg.add_text("QUEST COMPLETED!", color=(0, 255, 100))
            dpg.add_separator()
            with dpg.group(tag="quest_list"):
                pass

        with dpg.window(label="Add Game", modal=True, show=False, tag="add_game_modal", width=400, height=200):
            dpg.add_input_text(label="Place ID", width=-1, tag="new_place_id")
            dpg.add_input_text(label="Game Name", width=-1, tag="new_game_name")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Add", width=150, callback=lambda: [
                    self.add_game_to_grid(dpg.get_value("new_place_id"), dpg.get_value("new_game_name")),
                    dpg.configure_item("add_game_modal", show=False)
                ])
                dpg.add_button(label="Cancel", width=150, callback=lambda: dpg.configure_item("add_game_modal", show=False))

        with dpg.window(label="Popular Games", modal=True, show=False, tag="popular_games_modal", width=500, height=400):
            dpg.add_text("Click to add popular games:", color=(255, 200, 0))
            dpg.add_separator()
            with dpg.child_window(height=300):
                for name, game_data in POPULAR_GAMES.items():
                    def make_popular_callback(place_id, game_name):
                        def callback(s, a):
                            self.add_game_to_grid(place_id, game_name)
                            dpg.configure_item("popular_games_modal", show=False)
                        return callback
                    dpg.add_button(label=f"{name} (ID: {game_data['place_id']})", width=-1, height=30,
                                 callback=make_popular_callback(game_data["place_id"], game_data["name"]))

        # Initialize tkinter root (hidden) for filedialog
        try:
            root = Tk()
            root.withdraw()
        except:
            pass
        
        dpg.create_viewport(title=APP_NAME, width=950, height=650, resizable=False)
        dpg.setup_dearpygui()
        dpg.show_viewport()
        dpg.set_primary_window("main", True)
        self.apply_theme(self.config["theme"])
        self.update_theme_ui()
        
        # Initialize game grid after a short delay to ensure UI is ready
        def init_grid():
            try:
                if dpg.does_item_exist("game_grid"):
                    self.refresh_game_grid()
            except Exception as e:
                print(f"Error initializing grid: {e}")
        
        # Initialize immediately if possible, otherwise use timer
        try:
            if dpg.does_item_exist("game_grid"):
                self.refresh_game_grid()
        except:
            threading.Timer(0.2, init_grid).start()
        
        dpg.start_dearpygui()
        dpg.destroy_context()

if __name__ == "__main__":
    try: Buttstrapper().run()
    except Exception as e: print(e); input()
