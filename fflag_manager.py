import dearpygui.dearpygui as dpg
import json, threading, time, os, webbrowser, glob, shutil, re, sys
from pathlib import Path
from datetime import datetime
from pypresence import Presence
from PIL import Image

APP_NAME = "Buttstrapper Project"
VERSION = "2.1.1-ULTRA"
CLIENT_ID = "1455620291920265432"
MAX_SLOTS = 15

DEFAULT_CONFIG = {
    "fps": "165", 
    "graphics_level": 10, 
    "v_sync": False, 
    "no_shadows": False,
    "no_textures": False, 
    "disable_post_fx": False, 
    "full_resolution": True,
    "low_latency": True, 
    "lighting": "Future", 
    "theme": "Femboy",
    "games": [{"id": "", "name": "EMPTY SLOT", "thumb": ""} for _ in range(MAX_SLOTS)],
    "custom_flags": {},
    "flags": {
        "FFlagDebugGraphicsPreferD3D11": "True",
        "DFIntTaskSchedulerTargetFps": "165",
        "FFlagVisualEngineDisablePostProcess": "False"
    }
}

GENRE_LISTS = {
    "Combat & Battle": [
        ("10449761463", "The Strongest Battlegrounds"), ("12329385626", "Heroes Battlegrounds"),
        ("13597444155", "Sorcerer Battlegrounds"), ("14841165151", "Jujutsu Shenanigans"),
        ("11153120150", "Cursed Battlegrounds"), ("15832104523", "Saitama Battlegrounds"),
        ("178704642", "Combat Warriors"), ("2377868063", "Anime Dimensions")
    ],
    "FPS & Tactical": [
        ("286090429", "Arsenal"), ("292439477", "Phantom Forces"),
        ("606849621", "Bad Business"), ("111311599", "Typical Colors 2"),
        ("801323334", "Zombie Uprising"), ("113491250", "Unit 1968"),
        ("1168263273", "Energy Assault"), ("3233834335", "Frontlines")
    ],
    "Social & Fun": [
        ("1686885941", "Brookhaven RP"), ("537413528", "Build A Boat"),
        ("6516141723", "Doors"), ("155615604", "Prison Life"),
        ("370731277", "MeepCity"), ("10712613168", "Berry Avenue"),
        ("920587430", "Murder Mystery 2"), ("142823291", "Natural Disaster")
    ]
}

THEMES = {
    "Femboy": {"win": (255, 180, 210), "child": (255, 210, 230), "text": (90, 30, 60), "btn": (255, 130, 170), "accent": (255, 60, 130)},
    "Gay": {"win": (15, 15, 15), "child": (30, 30, 30), "text": (255, 255, 255), "btn": (50, 50, 50), "accent": (255, 50, 50)},
    "Simple Dark": {"win": (25, 25, 25), "child": (35, 35, 35), "text": (230, 230, 230), "btn": (50, 50, 50), "accent": (0, 150, 255)},
    "Simple Light": {"win": (240, 240, 240), "child": (255, 255, 255), "text": (30, 30, 30), "btn": (210, 210, 210), "accent": (0, 120, 215)},
    "Simple": {"win": (30, 32, 38), "child": (42, 45, 52), "text": (240, 240, 240), "btn": (60, 65, 80), "accent": (0, 153, 255)}
}

class ButtstrapApp:
    def __init__(self):
        self.root_dir = Path(os.path.expanduser("~")) / ".Buttstrap20"
        self.cache_dir = self.root_dir / "cache"
        self.root_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.config = self.load_and_fix_config()
        self.roblox_path = self.find_roblox()
        self.active_slot = 0
        self.current_tab = "DASHBOARD"

    def load_and_fix_config(self):
        p = self.root_dir / "config.json"
        cfg = DEFAULT_CONFIG.copy()
        if p.exists():
            try:
                with open(p, "r") as f:
                    loaded = json.load(f)
                    # Merge main keys
                    for key in loaded:
                        if key != "games":
                            cfg[key] = loaded[key]
                    # Specific merge for games to prevent IndexError
                    if "games" in loaded:
                        for i, g in enumerate(loaded["games"]):
                            if i < MAX_SLOTS:
                                cfg["games"][i].update(g)
            except: pass
        return cfg

    def save_config(self):
        with open(self.root_dir / "config.json", "w") as f:
            json.dump(self.config, f, indent=4)

    def log(self, msg, level="INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        if dpg.does_item_exist("console"):
            color = (255, 255, 255)
            if level == "ERROR": color = (255, 100, 100)
            elif level == "SUCCESS": color = (100, 255, 100)
            dpg.add_text(f"[{ts}] [{level}] {msg}", parent="console", color=color)
            dpg.set_y_scroll("console", -1.0)

    def find_roblox(self):
        pts = [os.path.expandvars(r"%LocalAppData%\Roblox\Versions\*"), os.path.expandvars(r"%LocalAppData%\Bloxstrap\Versions\*")]
        for p in pts:
            v = sorted(glob.glob(p), key=os.path.getmtime, reverse=True)
            for path in v:
                if (Path(path) / "RobloxPlayerBeta.exe").exists(): return path
        return ""

    def apply_fflags(self):
        if not self.roblox_path:
            self.log("ROBLOX NOT FOUND. Check your manual path in Config.", "ERROR")
            return
        
        cs = Path(self.roblox_path) / "ClientSettings"
        cs.mkdir(exist_ok=True)
        
        final_flags = self.config["flags"].copy()
        # Merge custom manual flags
        if self.config.get("custom_flags"):
            final_flags.update(self.config["custom_flags"])
        
        # Merge Tuner Settings
        final_flags.update({
            "DFIntTaskSchedulerTargetFps": str(self.config["fps"]),
            "FIntDebugForceInitializeGraphicsQuality": str(self.config["graphics_level"]),
            "FFlagVsyncEnabled": "True" if self.config["v_sync"] else "False",
            "FFlagGraphicsEnableReflexLowLatency": "True" if self.config["low_latency"] else "False",
            "DFFlagDisableDPIScale": "True" if self.config["full_resolution"] else "False",
            "FFlagVisualEngineDisablePostProcess": "True" if self.config["disable_post_fx"] else "False"
        })
        
        if self.config["no_shadows"]: final_flags["FIntRenderShadowIntensity"] = "0"
        if self.config["no_textures"]: final_flags["FIntTextureQualityOverride"] = "0"
        
        try:
            with open(cs / "ClientAppSettings.json", "w") as j:
                json.dump(final_flags, j, indent=4)
            self.log(f"Injected FFlags to: {cs.name}", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to write: {e}", "ERROR")

    def init_rpc(self):
        def rpc_run():
            try:
                rpc = Presence(CLIENT_ID)
                rpc.connect()
                while True:
                    rpc.update(state=f"Managing {self.current_tab}", details=f"Buttstrapper v{VERSION}", large_image="logo")
                    time.sleep(15)
            except: pass
        threading.Thread(target=rpc_run, daemon=True).start()

    def load_tex(self, path, tag):
        try:
            img = Image.open(path).convert("RGBA").resize((160, 90))
            data = [x / 255.0 for x in list(img.getdata()) for x in tuple(x)]
            if dpg.does_item_exist(tag): dpg.delete_item(tag)
            dpg.add_static_texture(width=160, height=90, default_value=data, tag=tag, parent="tex_reg")
            return True
        except: return False

    def pick_img(self, s, a):
        p = a['file_path_name']
        d = self.cache_dir / f"slot_{self.active_slot}{os.path.splitext(p)[1]}"
        shutil.copy(p, d)
        self.config["games"][self.active_slot]["thumb"] = str(d)
        self.load_tex(d, f"tx_{self.active_slot}")
        self.log(f"Updated icon for Slot {self.active_slot}")

    def save_slot(self):
        v = dpg.get_value("mid_in")
        m = re.search(r"(\d+)", v)
        pid = m.group(1) if m else v
        self.config["games"][self.active_slot].update({"id": pid, "name": dpg.get_value("mnm_in")})
        self.save_config()
        dpg.set_value(f"ls_{self.active_slot}", dpg.get_value("mnm_in"))
        dpg.configure_item("s_mod", show=False)
        self.log(f"Slot {self.active_slot} configured.")

    def set_theme(self, n):
        self.config["theme"] = n
        t = THEMES.get(n, THEMES["Femboy"])
        with dpg.theme() as gt:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, t["win"])
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, t["child"])
                dpg.add_theme_color(dpg.mvThemeCol_Text, t["text"])
                dpg.add_theme_color(dpg.mvThemeCol_Button, t["btn"])
                dpg.add_theme_color(dpg.mvThemeCol_Header, t["accent"])
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, t["btn"])
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, t["accent"])
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, t["accent"])
        dpg.bind_theme(gt)
        self.save_config()

    def run(self):
        dpg.create_context()
        with dpg.texture_registry(tag="tex_reg", show=False):
            ph = [0.1, 0.1, 0.1, 1.0] * (160 * 90)
            for i in range(MAX_SLOTS):
                tag = f"tx_{i}"
                th = self.config["games"][i].get("thumb", "")
                if not (th and os.path.exists(th) and self.load_tex(th, tag)):
                    dpg.add_static_texture(width=160, height=90, default_value=ph, tag=tag)

        with dpg.window(tag="Main", no_title_bar=True):
            with dpg.group(horizontal=True):
                dpg.add_text(f"{APP_NAME}", color=THEMES["Femboy"]["accent"])
                dpg.add_spacer(width=20)
                dpg.add_combo(list(THEMES.keys()), width=130, default_value=self.config["theme"], callback=lambda s,a: self.set_theme(a))
                dpg.add_text(f"v{VERSION}", color=(100,100,100))
            
            dpg.add_separator()
            with dpg.group(horizontal=True):
                for t, n in [("t_dash", "DASHBOARD"), ("t_tuner", "TUNER"), ("t_custom", "FLAGS"), ("t_set", "CONFIG")]:
                    dpg.add_button(label=n, width=145, height=32, callback=lambda s,a,u: [dpg.configure_item(x, show=False) for x in ["t_dash", "t_tuner", "t_custom", "t_set"]] + [dpg.configure_item(u[0], show=True), setattr(self, "current_tab", u[1])], user_data=(t, n))
            
            dpg.add_separator()
            with dpg.child_window(tag="ca", border=False, height=420):
                # Dashboard
                with dpg.group(tag="t_dash"):
                    with dpg.group(horizontal=True):
                        for g, gs in GENRE_LISTS.items():
                            dpg.add_button(label=g, width=130)
                            with dpg.popup(dpg.last_item(), mousebutton=dpg.mvMouseButton_Left):
                                for pid, nm in gs: dpg.add_menu_item(label=nm, callback=lambda s,a,u: [dpg.set_value("mid_in", u[0]), dpg.set_value("mnm_in", u[1]), self.save_slot()], user_data=(pid, nm))
                    
                    dpg.add_spacer(height=10)
                    with dpg.child_window(horizontal_scrollbar=True, height=210, border=False):
                        with dpg.group(horizontal=True):
                            for i in range(MAX_SLOTS):
                                with dpg.child_window(width=180, height=190, border=True):
                                    dpg.add_image(f"tx_{i}", width=160, height=85)
                                    dpg.add_text(self.config["games"][i]["name"], tag=f"ls_{i}", wrap=160)
                                    with dpg.group(horizontal=True):
                                        dpg.add_button(label="LAUNCH", width=75, callback=lambda s,a,u: [self.apply_fflags(), webbrowser.open(f"roblox://experiences/start?placeId={self.config['games'][u]['id']}")], user_data=i)
                                        dpg.add_button(label="EDIT", width=75, callback=lambda s,a,u: [setattr(self, "active_slot", u), dpg.set_value("mid_in", self.config["games"][u]["id"]), dpg.set_value("mnm_in", self.config["games"][u]["name"]), dpg.configure_item("s_mod", show=True)], user_data=i)

                # Tuner
                with dpg.group(tag="t_tuner", show=False):
                    dpg.add_text("ENGINE TUNER - FFLAGS")
                    dpg.add_slider_int(label="Graphics Level", min_value=1, max_value=21, default_value=self.config["graphics_level"], callback=lambda s,a: self.config.update({"graphics_level": a}))
                    dpg.add_input_text(label="FPS Limit", default_value=self.config["fps"], callback=lambda s,a: self.config.update({"fps": a}))
                    with dpg.group(horizontal=True):
                        for k, l in [("no_shadows", "No Shadows"), ("no_textures", "No Textures")]:
                            dpg.add_checkbox(label=l, default_value=self.config[k], callback=lambda s,a,u=k: self.config.update({u: a}))
                    with dpg.group(horizontal=True):
                        for k, l in [("disable_post_fx", "No PostFX"), ("v_sync", "V-Sync")]:
                            dpg.add_checkbox(label=l, default_value=self.config[k], callback=lambda s,a,u=k: self.config.update({u: a}))
                    for k, l in [("low_latency", "Reflex Latency"), ("full_resolution", "Native Resolution")]:
                         dpg.add_checkbox(label=l, default_value=self.config[k], callback=lambda s,a,u=k: self.config.update({u: a}))
                    
                    dpg.add_combo(["Future", "ShadowMap", "Voxel"], label="Lighting", default_value=self.config["lighting"], callback=lambda s,a: self.config.update({"lighting": a}))
                    dpg.add_button(label="APPLY TUNER SETTINGS", width=-1, height=40, callback=self.apply_fflags)

                # Custom Flags
                with dpg.group(tag="t_custom", show=False):
                    dpg.add_text("MANUAL JSON OVERRIDE")
                    dpg.add_input_text(tag="custom_json", multiline=True, height=280, width=-1, default_value=json.dumps(self.config.get("custom_flags", {}), indent=4))
                    dpg.add_button(label="PARSE & COMMIT FLAGS", width=-1, height=35, callback=lambda: [self.config.update({"custom_flags": json.loads(dpg.get_value("custom_json"))}), self.save_config(), self.log("Custom flags committed to config.")])

                # Config
                with dpg.group(tag="t_set", show=False):
                    dpg.add_text("APP CONFIGURATION")
                    dpg.add_input_text(label="Roblox/Bloxstrap Path", default_value=self.roblox_path, callback=lambda s,a: setattr(self, "roblox_path", a))
                    dpg.add_button(label="SAVE ALL CHANGES", width=-1, height=35, callback=self.save_config)
                    dpg.add_button(label="RESET CONFIG", width=-1, height=35, callback=lambda: [shutil.rmtree(self.root_dir), self.log("Config deleted. Restart app.")])

            dpg.add_separator()
            dpg.add_text("SYSTEM LOGS")
            dpg.add_child_window(tag="console", height=160, border=True)

        with dpg.file_dialog(show=False, callback=self.pick_img, tag="f_dlg", width=550, height=400): 
            dpg.add_file_extension(".png"); dpg.add_file_extension(".jpg"); dpg.add_file_extension(".*")
            
        with dpg.window(label="Slot Configuration", modal=True, show=False, tag="s_mod", width=380):
            dpg.add_input_text(label="PlaceID / Link", tag="mid_in")
            dpg.add_input_text(label="Display Name", tag="mnm_in")
            dpg.add_button(label="Change Icon", width=-1, callback=lambda: dpg.show_item("f_dlg"))
            dpg.add_button(label="SAVE SLOT", width=-1, callback=self.save_slot)

        self.set_theme(self.config["theme"])
        dpg.create_viewport(title="Buttstrapper v2.1.1", width=620, height=750, resizable=False)
        dpg.setup_dearpygui(); dpg.show_viewport(); dpg.set_primary_window("Main", True); self.init_rpc(); dpg.start_dearpygui(); dpg.destroy_context()

if __name__ == "__main__":
    ButtstrapApp().run()
