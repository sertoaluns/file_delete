# -*- coding: utf-8 -*-
"""
Tam Ekran Video Oynatıcı / Full Screen Video Player
Pop-up / Çerçevesiz Video Oynatıcı Masaüstü Uygulaması (Windows)
"""

import os
import sys
import json
import time
import threading
import subprocess
import ctypes
from ctypes import wintypes
import tkinter as tk
import customtkinter as ctk

# ==========================================
# 1. DPI FARKINDALIĞI VE WIN32 YAPILANDIRMASI
# ==========================================
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
shcore = getattr(ctypes.windll, 'shcore', None)

try:
    if shcore and hasattr(shcore, 'SetProcessDpiAwareness'):
        shcore.SetProcessDpiAwareness(2)  # Per-Monitor DPI aware
    else:
        user32.SetProcessDPIAware()
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

# Win32 Yapıları
class RECT(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.LONG),
        ("top", wintypes.LONG),
        ("right", wintypes.LONG),
        ("bottom", wintypes.LONG)
    ]

class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG)
    ]

class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD)
    ]

# Win32 Fonksiyon Tipleri
user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
user32.GetAncestor.restype = wintypes.HWND
user32.GetForegroundWindow.restype = wintypes.HWND
user32.SetWindowRgn.argtypes = [wintypes.HWND, wintypes.HRGN, wintypes.BOOL]
user32.SetWindowRgn.restype = wintypes.INT
gdi32.CreateRectRgn.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int]
gdi32.CreateRectRgn.restype = wintypes.HRGN
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

try:
    user32.WindowFromPoint.argtypes = [POINT]
    user32.WindowFromPoint.restype = wintypes.HWND
except Exception:
    pass

# Win32 Sabitleri
GA_ROOT = 2
GWL_EXSTYLE = -20
WS_EX_NOACTIVATE = 0x08000000
WS_EX_TOOLWINDOW = 0x00000080
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
HWND_TOPMOST = wintypes.HWND(-1)
HWND_NOTOPMOST = wintypes.HWND(-2)
WM_CLOSE = 0x0010
MONITOR_DEFAULTTONEAREST = 2

VK_CONTROL = 0x11
VK_SHIFT = 0x10
VK_T = 0x54
VK_R = 0x52
VK_B = 0x42

def get_window_from_point(x, y):
    """Verilen ekran noktasındaki pencereyi döner (64-bit uyumlu)."""
    pt = POINT(x, y)
    try:
        return user32.WindowFromPoint(pt)
    except Exception:
        val = (ctypes.c_uint64(y).value << 32) | ctypes.c_uint64(x).value
        return user32.WindowFromPoint(val)

# ==========================================
# 2. DİL, AYARLAR VE TARAYICI YOLU YÖNETİMİ
# ==========================================
APP_DIR = os.path.dirname(os.path.abspath(__file__))
LANG_DIR = os.path.join(APP_DIR, "lang")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
PROFILE_DIR = os.path.join(APP_DIR, "profil")

DEFAULT_SETTINGS = {
    "language": "tr",
    "recent_links": [],
    "last_window": {
        "x": None,
        "y": None,
        "width": 1280,
        "height": 720
    },
    "borderless": True,
    "always_on_top": False
}

def get_available_languages():
    """lang/ klasöründeki mevcut dilleri tarar."""
    langs = []
    if os.path.exists(LANG_DIR):
        for f in os.listdir(LANG_DIR):
            if f.endswith(".json"):
                langs.append(os.path.splitext(f)[0])
    if not langs:
        langs = ["tr", "en"]
    return sorted(langs)

def load_language_dict(lang_code):
    """Belirtilen dil dosyasını yükler."""
    file_path = os.path.join(LANG_DIR, f"{lang_code}.json")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def load_settings():
    """Ayar dosyasını yükler, yoksa varsayılanı döner."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {**DEFAULT_SETTINGS, **data}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    """Ayarları JSON dosyasına kaydeder."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def find_browser_path():
    """Chrome veya Edge yürütülebilir dosyasını bulur."""
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")

    candidate_paths = [
        # Chrome
        os.path.join(prog_files, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(prog_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe"),
        # Edge
        os.path.join(prog_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(prog_files, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe")
    ]

    for p in candidate_paths:
        if p and os.path.isfile(p):
            return p
    return None

# ==========================================
# 3. YARDIMCI WIN32 METOTLARI
# ==========================================
def get_monitor_work_area(hwnd):
    """Pencerenin bulunduğu monitörün çalışma alanını döner."""
    hmon = user32.MonitorFromWindow(hwnd, MONITOR_DEFAULTTONEAREST)
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    if user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
        return (
            mi.rcWork.left,
            mi.rcWork.top,
            mi.rcWork.right - mi.rcWork.left,
            mi.rcWork.bottom - mi.rcWork.top,
            mi.rcMonitor.right - mi.rcMonitor.left,
            mi.rcMonitor.bottom - mi.rcMonitor.top
        )
    return (0, 0, 1920, 1080, 1920, 1080)

def is_window_max_or_fullscreen(hwnd):
    """Pencerenin maximize, minimize veya tam ekran olup olmadığını kontrol eder."""
    if not hwnd or not user32.IsWindow(hwnd):
        return False
    if user32.IsIconic(hwnd) or user32.IsZoomed(hwnd):
        return True
    
    # Monitör boyutu ile karşılaştır
    wrect = RECT()
    if user32.GetWindowRect(hwnd, ctypes.byref(wrect)):
        ww = wrect.right - wrect.left
        wh = wrect.bottom - wrect.top
        _, _, _, _, mon_w, mon_h = get_monitor_work_area(hwnd)
        if ww >= mon_w and wh >= mon_h:
            return True
    return False

def apply_borderless_region(hwnd, enable=True):
    """İstemci alanını kırparak başlık çubuğu ve kenarlıkları gizler."""
    if not hwnd or not user32.IsWindow(hwnd):
        return

    if not enable or is_window_max_or_fullscreen(hwnd):
        # Bölgeyi kaldır, varsayılan görünüm
        user32.SetWindowRgn(hwnd, 0, True)
        return

    wrect = RECT()
    crect = RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(wrect)):
        return
    if not user32.GetClientRect(hwnd, ctypes.byref(crect)):
        return

    pt = POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))

    offset_x = pt.x - wrect.left
    offset_y = pt.y - wrect.top
    client_w = crect.right - crect.left
    client_h = crect.bottom - crect.top

    if client_w <= 0 or client_h <= 0:
        return

    hrgn = gdi32.CreateRectRgn(offset_x, offset_y, offset_x + client_w, offset_y + client_h)
    if hrgn:
        user32.SetWindowRgn(hwnd, hrgn, True)

# ==========================================
# 4. ANA UYGULAMA SINIFI
# ==========================================
class PopupVideoPlayerApp:
    def __init__(self):
        # Ayarları yükle
        self.settings = load_settings()
        self.borderless_mode = self.settings.get("borderless", True)
        self.always_on_top = self.settings.get("always_on_top", False)

        # Çoklu Dil (i18n) Başlatma
        self.current_lang = self.settings.get("language", "tr")
        self.lang_dict = load_language_dict(self.current_lang)
        self.fallback_dict = load_language_dict("tr") if self.current_lang != "tr" else load_language_dict("en")

        # Durum Değişkenleri
        self.chrome_hwnd = None
        self.chrome_proc = None
        self.is_monitoring = False
        self.is_dragging = False
        self.drag_mode = None
        self.drag_start_cur = (0, 0)
        self.drag_start_win = (0, 0)
        self.drag_info = {}

        # Tutma barı animasyon ve gizleme sayaçları
        self.bar_state = "closed"  # 'closed', 'opening', 'open', 'closing'
        self.bar_target_h = 34
        self.bar_current_h = 0
        self.anim_start_time = 0
        self.last_hover_pos = (0, 0)
        self.last_hover_time = 0
        self.left_bar_time = None
        self.cooldown_until = 0

        # GUI Başlatma
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title(self.t("app_title"))
        self.init_main_window()
        self.init_top_bar()

        # Klavye kısayolları thread'i
        self.app_running = True
        self.shortcut_thread = threading.Thread(target=self.shortcut_listener, daemon=True)
        self.shortcut_thread.start()

        # 16:9 oran izleme thread'i
        self.aspect_thread = threading.Thread(target=self.aspect_ratio_monitor, daemon=True)
        self.aspect_thread.start()

        # Tutma barı güncelleme döngüsü (ana thread)
        self.root.after(15, self.bar_update_loop)
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)

    def t(self, key, **kwargs):
        """Mevcut dildeki metni döner, yoksa fallback diline başvurur."""
        val = self.lang_dict.get(key, self.fallback_dict.get(key, key))
        if kwargs:
            try:
                val = val.format(**kwargs)
            except Exception:
                pass
        return val

    def init_main_window(self):
        """Arayüz 1: Link giriş ekranı."""
        w, h = 600, 310
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - w) // 2)
        y = max(0, (sh - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(False, False)

        # Ana Kapsayıcı Frame
        main_frame = ctk.CTkFrame(self.root, corner_radius=12, fg_color="#18181b")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Üst Satır: Başlık & Dil Seçici
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(15, 12))

        self.title_label = ctk.CTkLabel(
            header_frame,
            text=self.t("title"),
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color="#F4F4F5"
        )
        self.title_label.pack(side="left")

        # Dinamik Dil Seçici (lang/ klasöründeki tüm dilleri listeler)
        available_langs = [l.upper() for l in get_available_languages()]
        current_lang_display = self.current_lang.upper() if self.current_lang.upper() in available_langs else (available_langs[0] if available_langs else "TR")

        self.lang_menu = ctk.CTkOptionMenu(
            header_frame,
            values=available_langs,
            width=65,
            height=26,
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#27272a",
            button_color="#3f3f46",
            button_hover_color="#52525b",
            corner_radius=6,
            command=self.on_language_changed
        )
        self.lang_menu.set(current_lang_display)
        self.lang_menu.pack(side="right")

        # Link Giriş Satırı (Entry + Yapıştır butonu)
        entry_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        entry_row.pack(fill="x", padx=25, pady=(0, 8))

        self.link_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text=self.t("placeholder_link"),
            height=38,
            font=ctk.CTkFont(size=13),
            corner_radius=8
        )
        self.link_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.link_entry.bind("<Return>", lambda e: self.on_open_clicked())

        self.paste_btn = ctk.CTkButton(
            entry_row,
            text=self.t("btn_paste"),
            width=80,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#27272a",
            hover_color="#3f3f46",
            corner_radius=8,
            command=self.on_paste_clicked
        )
        self.paste_btn.pack(side="right")

        # Son Linkler Açılır Menüsü
        self.recent_combo = ctk.CTkComboBox(
            main_frame,
            values=[""],
            height=32,
            font=ctk.CTkFont(size=12),
            corner_radius=8,
            command=self.on_recent_selected
        )
        self.update_recent_combo()
        self.recent_combo.pack(fill="x", padx=25, pady=(0, 10))

        # Onay Kutusu: Gerçek tam ekran (F11)
        self.fullscreen_var = tk.BooleanVar(value=False)
        self.fullscreen_cb = ctk.CTkCheckBox(
            main_frame,
            text=self.t("chk_fullscreen"),
            variable=self.fullscreen_var,
            font=ctk.CTkFont(size=13),
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=4
        )
        self.fullscreen_cb.pack(pady=(0, 12))

        # AÇ Butonu
        self.open_btn = ctk.CTkButton(
            main_frame,
            text=self.t("btn_open"),
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            corner_radius=8,
            command=self.on_open_clicked
        )
        self.open_btn.pack(fill="x", padx=25, pady=(0, 6))

        # Hata / Uyarı Etiketi
        self.error_label = ctk.CTkLabel(
            main_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#EF4444"
        )
        self.error_label.pack(pady=(0, 5))

    def on_language_changed(self, choice):
        """Kullanıcı yeni bir dil seçtiğinde tüm arayüzü anında günceller."""
        new_lang = choice.lower()
        self.current_lang = new_lang
        self.settings["language"] = new_lang
        save_settings(self.settings)

        self.lang_dict = load_language_dict(self.current_lang)
        self.fallback_dict = load_language_dict("tr") if self.current_lang != "tr" else load_language_dict("en")

        self.update_ui_texts()

    def update_ui_texts(self):
        """Arayüz metinlerini seçilen dile göre günceller."""
        self.root.title(self.t("app_title"))
        self.title_label.configure(text=self.t("title"))
        self.link_entry.configure(placeholder_text=self.t("placeholder_link"))
        self.paste_btn.configure(text=self.t("btn_paste"))
        self.fullscreen_cb.configure(text=self.t("chk_fullscreen"))
        self.open_btn.configure(text=self.t("btn_open"))
        self.update_recent_combo()

    def update_recent_combo(self):
        """Geçmiş linkler menüsünü günceller."""
        recent = self.settings.get("recent_links", [])
        if recent:
            self.recent_combo.configure(values=recent)
            self.recent_combo.set(self.t("recent_header"))
        else:
            self.recent_combo.configure(values=[self.t("recent_empty")])
            self.recent_combo.set(self.t("recent_header"))

    def on_paste_clicked(self):
        """Panodaki metni link kutusuna yapıştırır."""
        try:
            clipboard_text = self.root.clipboard_get()
            if clipboard_text:
                self.link_entry.delete(0, tk.END)
                self.link_entry.insert(0, clipboard_text.strip())
                self.error_label.configure(text="")
        except Exception:
            pass

    def on_recent_selected(self, choice):
        """Açılır menüden bir link seçildiğinde kutuya aktarır."""
        if choice and choice != self.t("recent_empty") and choice != self.t("recent_header"):
            self.link_entry.delete(0, tk.END)
            self.link_entry.insert(0, choice)
            self.error_label.configure(text="")

    def init_top_bar(self):
        """Üstten açılan tutma barı penceresi (Toplevel)."""
        self.bar = tk.Toplevel(self.root)
        self.bar.withdraw()
        self.bar.overrideredirect(True)
        self.bar.wm_attributes("-topmost", True)
        self.bar.wm_attributes("-alpha", 0.94)
        self.bar.configure(bg="#18181b")

        # Win32 stil ayarı: Odak çalmasın, görev çubuğunda simgesi görünmesin
        self.bar.update_idletasks()
        bar_hwnd = user32.GetParent(self.bar.winfo_id())
        if not bar_hwnd:
            bar_hwnd = self.bar.winfo_id()
        self.bar_hwnd = bar_hwnd

        try:
            ex_style = user32.GetWindowLongW(bar_hwnd, GWL_EXSTYLE)
            user32.SetWindowLongW(bar_hwnd, GWL_EXSTYLE, ex_style | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)
        except Exception:
            pass

        # Bar İçeriği
        container = tk.Frame(self.bar, bg="#18181b")
        container.pack(fill="both", expand=True)

        # 1. Sol Boyutlandırma Tutamacı (sol uç)
        self.left_handle = tk.Label(
            container,
            text="⤡",
            bg="#18181b",
            fg="#9CA3AF",
            font=("Segoe UI Symbol", 12, "bold"),
            width=4,
            cursor="size_nw_se"
        )
        self.left_handle.pack(side="left", fill="y")
        self.left_handle.bind("<ButtonPress-1>", self.on_resize_left_start)
        self.left_handle.bind("<B1-Motion>", self.on_resize_left_motion)
        self.left_handle.bind("<ButtonRelease-1>", self.on_drag_release)

        # 2. Sağ Taraf Butonları & Sağ Boyutlandırma Tutamacı
        # Sağ Tutamaç
        self.right_handle = tk.Label(
            container,
            text="⤢",
            bg="#18181b",
            fg="#9CA3AF",
            font=("Segoe UI Symbol", 12, "bold"),
            width=4,
            cursor="size_ne_sw"
        )
        self.right_handle.pack(side="right", fill="y")
        self.right_handle.bind("<ButtonPress-1>", self.on_resize_right_start)
        self.right_handle.bind("<B1-Motion>", self.on_resize_right_motion)
        self.right_handle.bind("<ButtonRelease-1>", self.on_drag_release)

        # Kapat Butonu (X)
        self.close_btn = tk.Label(
            container,
            text="✕",
            bg="#18181b",
            fg="#E4E4E7",
            font=("Segoe UI", 11, "bold"),
            width=3,
            cursor="hand2"
        )
        self.close_btn.pack(side="right", fill="y")
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.configure(bg="#DC2626", fg="#FFFFFF"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.configure(bg="#18181b", fg="#E4E4E7"))
        self.close_btn.bind("<Button-1>", lambda e: self.close_chrome_window())

        # Her Zaman Üstte Butonu (İğne)
        self.pin_btn = tk.Label(
            container,
            text="📌",
            bg="#2563EB" if self.always_on_top else "#18181b",
            fg="#FFFFFF" if self.always_on_top else "#9CA3AF",
            font=("Segoe UI Symbol", 10),
            width=3,
            cursor="hand2"
        )
        self.pin_btn.pack(side="right", fill="y")
        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_always_on_top())

        # 3. Orta Taşıma Tutamacı (Geniş Alan)
        self.move_handle = tk.Frame(container, bg="#27272a", cursor="fleur")
        self.move_handle.pack(side="left", fill="both", expand=True)

        move_icon = tk.Label(
            self.move_handle,
            text="☰",
            bg="#27272a",
            fg="#71717A",
            font=("Segoe UI Symbol", 11, "bold"),
            cursor="fleur"
        )
        move_icon.pack(expand=True)

        # Sürükleme olaylarını bağla
        for widget in (self.move_handle, move_icon):
            widget.bind("<ButtonPress-1>", self.on_move_start)
            widget.bind("<B1-Motion>", self.on_move_motion)
            widget.bind("<ButtonRelease-1>", self.on_drag_release)

    # ==========================================
    # 5. TARAYICI BAŞLATMA VE YÖNETİM
    # ==========================================
    def on_open_clicked(self):
        """Link doğrulaması yapar ve video penceresini başlatır."""
        raw_link = self.link_entry.get().strip()
        if not raw_link:
            self.error_label.configure(text=self.t("err_empty_link"))
            return

        # https:// yoksa ekle
        if not (raw_link.startswith("http://") or raw_link.startswith("https://")):
            link = "https://" + raw_link
        else:
            link = raw_link

        browser_path = find_browser_path()
        if not browser_path:
            self.error_label.configure(text=self.t("err_browser_not_found"))
            return

        self.error_label.configure(text="")

        # Son linkleri güncelle ve kaydet
        recent = self.settings.get("recent_links", [])
        if link in recent:
            recent.remove(link)
        recent.insert(0, link)
        self.settings["recent_links"] = recent[:10]
        save_settings(self.settings)
        self.update_recent_combo()

        # Chrome komut parametreleri
        last_win = self.settings.get("last_window", {})
        win_w = last_win.get("width") or 1280
        win_h = last_win.get("height") or 720
        win_x = last_win.get("x")
        win_y = last_win.get("y")

        if not os.path.exists(PROFILE_DIR):
            try:
                os.makedirs(PROFILE_DIR, exist_ok=True)
            except Exception:
                pass

        cmd = [
            browser_path,
            f"--app={link}",
            f"--user-data-dir={PROFILE_DIR}",
            f"--window-size={win_w},{win_h}"
        ]
        if win_x is not None and win_y is not None:
            cmd.append(f"--window-position={win_x},{win_y}")

        if self.fullscreen_var.get():
            cmd.append("--start-fullscreen")

        try:
            # Mevcut Chrome pencerelerini tespit et
            existing_hwnds = self.get_existing_chrome_hwnds()

            # Process başlat
            self.chrome_proc = subprocess.Popen(cmd)

            # Arayüz 1 minimize et
            self.root.iconify()

            # Arka plan thread'inde pencereyi yakala
            threading.Thread(
                target=self.wait_and_attach_chrome,
                args=(existing_hwnds, win_x, win_y, win_w, win_h),
                daemon=True
            ).start()

        except Exception as e:
            self.root.deiconify()
            self.error_label.configure(text=self.t("err_launch_failed", error=str(e)))

    def get_existing_chrome_hwnds(self):
        """Mevcut Chrome pencerelerinin HWND kümesini döner."""
        existing = set()
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_cb(hwnd, lparam):
            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            if class_buf.value == "Chrome_WidgetWin_1":
                existing.add(hwnd)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
        return existing

    def wait_and_attach_chrome(self, existing_hwnds, pref_x, pref_y, pref_w, pref_h):
        """Yeni açılan Chrome penceresini yakalar ve yapılandırır."""
        start_time = time.time()
        found_hwnd = None
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_cb(hwnd, lparam):
            nonlocal found_hwnd
            if hwnd in existing_hwnds:
                return True
            if not user32.IsWindowVisible(hwnd):
                return True

            class_buf = ctypes.create_unicode_buffer(256)
            user32.GetClassNameW(hwnd, class_buf, 256)
            if class_buf.value == "Chrome_WidgetWin_1":
                found_hwnd = hwnd
                return False
            return True

        cb = WNDENUMPROC(enum_cb)

        while time.time() - start_time < 15.0:
            user32.EnumWindows(cb, 0)
            if found_hwnd:
                break
            time.sleep(0.5)

        if not found_hwnd:
            # Bulunamadıysa Arayüz 1'i geri getir
            self.root.after(0, lambda: (
                self.root.deiconify(),
                self.error_label.configure(text=self.t("err_window_not_found"))
            ))
            return

        self.chrome_hwnd = found_hwnd

        # İlk açılışta veya kayıtlı konum yoksa ekranın ortasında 1280x720 istemci alanıyla başlat
        if pref_x is None or pref_y is None:
            self.center_client_1280x720(found_hwnd)

        # "Her zaman üstte" durumunu uygula
        if self.always_on_top:
            user32.SetWindowPos(found_hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

        # Çerçevesiz modu uygula
        self.root.after(0, lambda: apply_borderless_region(self.chrome_hwnd, self.borderless_mode))

        # İzleme döngüsünü başlat
        self.is_monitoring = True
        self.monitor_chrome_lifecycle()

    def center_client_1280x720(self, hwnd):
        """Pencereyi 1280x720 istemci alanıyla ekranın ortasına yerleştirir."""
        work_x, work_y, work_w, work_h, _, _ = get_monitor_work_area(hwnd)

        wrect = RECT()
        crect = RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(wrect))
        user32.GetClientRect(hwnd, ctypes.byref(crect))

        cw = crect.right - crect.left
        ch = crect.bottom - crect.top
        border_w = (wrect.right - wrect.left) - cw
        border_h = (wrect.bottom - wrect.top) - ch

        target_cw = 1280
        target_ch = 720
        target_ww = target_cw + border_w
        target_wh = target_ch + border_h

        new_x = work_x + max(0, (work_w - target_ww) // 2)
        new_y = work_y + max(0, (work_h - target_wh) // 2)

        user32.SetWindowPos(hwnd, 0, new_x, new_y, target_ww, target_wh, SWP_NOZORDER | SWP_NOACTIVATE)

    def monitor_chrome_lifecycle(self):
        """Chrome penceresinin kapanmasını izler."""
        while self.is_monitoring and self.chrome_hwnd:
            if not user32.IsWindow(self.chrome_hwnd):
                break
            time.sleep(0.5)

        # Pencere kapandı
        self.chrome_hwnd = None
        self.is_monitoring = False
        self.root.after(0, self.on_chrome_closed)

    def on_chrome_closed(self):
        """Chrome penceresi kapandığında tutma barını gizler ve Arayüz 1'i gösterir."""
        self.bar.withdraw()
        self.bar_state = "closed"
        self.root.deiconify()

    def close_chrome_window(self):
        """Chrome penceresine kapatma mesajı gönderir."""
        if self.chrome_hwnd and user32.IsWindow(self.chrome_hwnd):
            user32.PostMessageW(self.chrome_hwnd, WM_CLOSE, 0, 0)

    # ==========================================
    # 6. TUTMA BARI HAREKET VE ANİMASYON DÖNGÜSÜ
    # ==========================================
    def bar_update_loop(self):
        """Her 15 ms'de bir çalışarak barın açılma/gizlenme ve konumunu yönetir."""
        try:
            if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
                if self.bar_state != "closed":
                    self.bar.withdraw()
                    self.bar_state = "closed"
                self.root.after(15, self.bar_update_loop)
                return

            # Tam ekran, minimize veya maximize durumunda barı gizle
            if is_window_max_or_fullscreen(self.chrome_hwnd) or not self.borderless_mode:
                if self.bar_state != "closed":
                    self.bar.withdraw()
                    self.bar_state = "closed"
                self.root.after(15, self.bar_update_loop)
                return

            # İstemci alanını al
            pt = POINT(0, 0)
            user32.ClientToScreen(self.chrome_hwnd, ctypes.byref(pt))
            crect = RECT()
            user32.GetClientRect(self.chrome_hwnd, ctypes.byref(crect))

            client_x = pt.x
            client_y = pt.y
            client_w = crect.right - crect.left

            # Fare konumunu al
            cur_pt = POINT()
            user32.GetCursorPos(ctypes.byref(cur_pt))
            cur_x, cur_y = cur_pt.x, cur_pt.y

            now = time.time()

            # Fare altındaki pencereyi doğrula
            hwnd_under = get_window_from_point(cur_x, cur_y)
            root_under = user32.GetAncestor(hwnd_under, GA_ROOT)
            is_over_chrome_or_bar = (
                root_under == self.chrome_hwnd or
                hwnd_under == self.bar_hwnd or
                root_under == self.bar_hwnd
            )

            # Açılma tetikleme alanı: İstemci alanının en üst 6 pikseli
            in_trigger_zone = (
                client_x <= cur_x <= client_x + client_w and
                client_y <= cur_y <= client_y + 6 and
                is_over_chrome_or_bar and
                now >= self.cooldown_until
            )

            # Durum Yönetimi
            if self.bar_state == "closed":
                if in_trigger_zone:
                    self.bar_state = "opening"
                    self.anim_start_time = now
                    self.bar_current_h = 0
                    self.bar.geometry(f"{client_w}x1+{client_x}+{client_y}")
                    self.bar.deiconify()

            elif self.bar_state == "opening":
                elapsed = now - self.anim_start_time
                progress = min(1.0, elapsed / 0.15)  # 150 ms
                self.bar_current_h = int(34 * progress)
                h = max(1, self.bar_current_h)
                self.bar.geometry(f"{client_w}x{h}+{client_x}+{client_y}")

                if progress >= 1.0:
                    self.bar_state = "open"
                    self.last_hover_pos = (cur_x, cur_y)
                    self.last_hover_time = now
                    self.left_bar_time = None

            elif self.bar_state == "open":
                # Bar açıkken konumu ve genişliği hizala
                if not self.is_dragging:
                    self.bar.geometry(f"{client_w}x34+{client_x}+{client_y}")

                # Sürükleme devam ediyorsa gizlenme sayacı çalışmaz
                if not self.is_dragging:
                    is_inside_bar = (
                        client_x <= cur_x <= client_x + client_w and
                        client_y <= cur_y <= client_y + 34
                    )

                    if is_inside_bar:
                        self.left_bar_time = None
                        # Hareket kontrolü (2 piksel)
                        if abs(cur_x - self.last_hover_pos[0]) > 2 or abs(cur_y - self.last_hover_pos[1]) > 2:
                            self.last_hover_pos = (cur_x, cur_y)
                            self.last_hover_time = now
                        elif now - self.last_hover_time >= 1.5:
                            # 1.5 saniye hareketsiz kaldı
                            self.bar_state = "closing"
                            self.anim_start_time = now
                    else:
                        if self.left_bar_time is None:
                            self.left_bar_time = now
                        elif now - self.left_bar_time >= 0.6:
                            # Bardan çıkalı 0.6 saniye oldu
                            self.bar_state = "closing"
                            self.anim_start_time = now

            elif self.bar_state == "closing":
                elapsed = now - self.anim_start_time
                progress = min(1.0, elapsed / 0.15)
                self.bar_current_h = int(34 * (1.0 - progress))
                h = max(1, self.bar_current_h)
                self.bar.geometry(f"{client_w}x{h}+{client_x}+{client_y}")

                if progress >= 1.0:
                    self.bar_state = "closed"
                    self.bar.withdraw()
                    self.cooldown_until = now + 0.3  # 300 ms tekrar açılmama garantisi

        except Exception:
            pass

        self.root.after(15, self.bar_update_loop)

    # ==========================================
    # 7. TAŞIMA VE BOYUTLANDIRMA ETKİLEŞİMLERİ
    # ==========================================
    def get_cursor_pos(self):
        """İmlecin mutlak koordinatlarını döner."""
        pt = POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return pt.x, pt.y

    def on_move_start(self, event):
        """Pencere taşıma başlangıcı."""
        if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
            return
        self.is_dragging = True
        self.drag_mode = "move"
        self.drag_start_cur = self.get_cursor_pos()

        wrect = RECT()
        user32.GetWindowRect(self.chrome_hwnd, ctypes.byref(wrect))
        self.drag_start_win = (wrect.left, wrect.top)

    def on_move_motion(self, event):
        """Pencere taşıma devam ederken pencereyi ve barı günceller."""
        if not self.is_dragging or self.drag_mode != "move" or not self.chrome_hwnd:
            return
        cur_x, cur_y = self.get_cursor_pos()
        dx = cur_x - self.drag_start_cur[0]
        dy = cur_y - self.drag_start_cur[1]

        new_x = self.drag_start_win[0] + dx
        new_y = self.drag_start_win[1] + dy

        user32.SetWindowPos(self.chrome_hwnd, 0, new_x, new_y, 0, 0, SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE)
        self.sync_bar_now()

    def on_resize_left_start(self, event):
        """Sol uçtan boyutlandırma başlangıcı (sağ ve üst kenar sabit)."""
        if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
            return
        self.is_dragging = True
        self.drag_mode = "resize_left"
        self.drag_start_cur = self.get_cursor_pos()

        wrect = RECT()
        crect = RECT()
        user32.GetWindowRect(self.chrome_hwnd, ctypes.byref(wrect))
        user32.GetClientRect(self.chrome_hwnd, ctypes.byref(crect))

        pt = POINT(0, 0)
        user32.ClientToScreen(self.chrome_hwnd, ctypes.byref(pt))

        client_x, client_y = pt.x, pt.y
        client_w = crect.right - crect.left
        client_h = crect.bottom - crect.top
        border_w = (wrect.right - wrect.left) - client_w
        border_h = (wrect.bottom - wrect.top) - client_h

        self.drag_info = {
            "fixed_right": client_x + client_w,
            "fixed_top": client_y,
            "start_cw": client_w,
            "offset_x": pt.x - wrect.left,
            "offset_y": pt.y - wrect.top,
            "border_w": border_w,
            "border_h": border_h
        }

    def on_resize_left_motion(self, event):
        """Sol uçtan boyutlandırma devamı (16:9 oranlı)."""
        if not self.is_dragging or self.drag_mode != "resize_left" or not self.chrome_hwnd:
            return
        cur_x, _ = self.get_cursor_pos()
        dx = cur_x - self.drag_start_cur[0]

        target_cw = self.drag_info["start_cw"] - dx

        # Sınırlar
        _, _, max_cw, max_ch, _, _ = get_monitor_work_area(self.chrome_hwnd)
        target_cw = max(640, min(max_cw, target_cw))
        target_ch = int(round(target_cw * 9 / 16))

        if target_ch > max_ch:
            target_ch = max_ch
            target_cw = int(round(target_ch * 16 / 9))
        if target_ch < 360:
            target_ch = 360
            target_cw = int(round(target_ch * 16 / 9))

        new_client_x = self.drag_info["fixed_right"] - target_cw
        new_client_y = self.drag_info["fixed_top"]

        win_x = new_client_x - self.drag_info["offset_x"]
        win_y = new_client_y - self.drag_info["offset_y"]
        win_w = target_cw + self.drag_info["border_w"]
        win_h = target_ch + self.drag_info["border_h"]

        user32.SetWindowPos(self.chrome_hwnd, 0, win_x, win_y, win_w, win_h, SWP_NOZORDER | SWP_NOACTIVATE)
        apply_borderless_region(self.chrome_hwnd, self.borderless_mode)
        self.sync_bar_now()

    def on_resize_right_start(self, event):
        """Sağ uçtan boyutlandırma başlangıcı (sol ve üst kenar sabit)."""
        if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
            return
        self.is_dragging = True
        self.drag_mode = "resize_right"
        self.drag_start_cur = self.get_cursor_pos()

        wrect = RECT()
        crect = RECT()
        user32.GetWindowRect(self.chrome_hwnd, ctypes.byref(wrect))
        user32.GetClientRect(self.chrome_hwnd, ctypes.byref(crect))

        pt = POINT(0, 0)
        user32.ClientToScreen(self.chrome_hwnd, ctypes.byref(pt))

        client_x, client_y = pt.x, pt.y
        client_w = crect.right - crect.left
        client_h = crect.bottom - crect.top
        border_w = (wrect.right - wrect.left) - client_w
        border_h = (wrect.bottom - wrect.top) - client_h

        self.drag_info = {
            "fixed_left": client_x,
            "fixed_top": client_y,
            "start_cw": client_w,
            "offset_x": pt.x - wrect.left,
            "offset_y": pt.y - wrect.top,
            "border_w": border_w,
            "border_h": border_h
        }

    def on_resize_right_motion(self, event):
        """Sağ uçtan boyutlandırma devamı (16:9 oranlı)."""
        if not self.is_dragging or self.drag_mode != "resize_right" or not self.chrome_hwnd:
            return
        cur_x, _ = self.get_cursor_pos()
        dx = cur_x - self.drag_start_cur[0]

        target_cw = self.drag_info["start_cw"] + dx

        _, _, max_cw, max_ch, _, _ = get_monitor_work_area(self.chrome_hwnd)
        target_cw = max(640, min(max_cw, target_cw))
        target_ch = int(round(target_cw * 9 / 16))

        if target_ch > max_ch:
            target_ch = max_ch
            target_cw = int(round(target_ch * 16 / 9))
        if target_ch < 360:
            target_ch = 360
            target_cw = int(round(target_ch * 16 / 9))

        win_x = self.drag_info["fixed_left"] - self.drag_info["offset_x"]
        win_y = self.drag_info["fixed_top"] - self.drag_info["offset_y"]
        win_w = target_cw + self.drag_info["border_w"]
        win_h = target_ch + self.drag_info["border_h"]

        user32.SetWindowPos(self.chrome_hwnd, 0, win_x, win_y, win_w, win_h, SWP_NOZORDER | SWP_NOACTIVATE)
        apply_borderless_region(self.chrome_hwnd, self.borderless_mode)
        self.sync_bar_now()

    def on_drag_release(self, event):
        """Taşıma veya boyutlandırma bırakıldığında son durumu kaydeder."""
        self.is_dragging = False
        self.drag_mode = None
        cur_x, cur_y = self.get_cursor_pos()
        self.last_hover_pos = (cur_x, cur_y)
        self.last_hover_time = time.time()

        if self.chrome_hwnd and user32.IsWindow(self.chrome_hwnd):
            apply_borderless_region(self.chrome_hwnd, self.borderless_mode)
            self.save_window_metrics()

    def sync_bar_now(self):
        """Barı anında Chrome penceresinin istemci alanının üzerine hizalar."""
        if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
            return
        pt = POINT(0, 0)
        user32.ClientToScreen(self.chrome_hwnd, ctypes.byref(pt))
        crect = RECT()
        user32.GetClientRect(self.chrome_hwnd, ctypes.byref(crect))
        client_w = crect.right - crect.left
        h = 34 if self.bar_state in ("open", "opening") else max(1, self.bar_current_h)
        self.bar.geometry(f"{client_w}x{h}+{pt.x}+{pt.y}")

    def save_window_metrics(self):
        """Mevcut pencere konumu ve boyutunu ayarlara kaydeder."""
        if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
            return
        wrect = RECT()
        if user32.GetWindowRect(self.chrome_hwnd, ctypes.byref(wrect)):
            self.settings["last_window"] = {
                "x": wrect.left,
                "y": wrect.top,
                "width": wrect.right - wrect.left,
                "height": wrect.bottom - wrect.top
            }
            save_settings(self.settings)

    # ==========================================
    # 8. 16:9 ORAN KORUMA DÖNGÜSÜ (THREAD)
    # ==========================================
    def aspect_ratio_monitor(self):
        """Arka planda pencere boyutunu izler ve 16:9 oranını korur."""
        prev_cw = None
        prev_ch = None

        while self.app_running:
            time.sleep(0.04)  # 40 ms
            if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
                prev_cw, prev_ch = None, None
                continue

            if self.is_dragging:
                continue

            if is_window_max_or_fullscreen(self.chrome_hwnd):
                continue

            crect = RECT()
            wrect = RECT()
            if not user32.GetClientRect(self.chrome_hwnd, ctypes.byref(crect)):
                continue
            if not user32.GetWindowRect(self.chrome_hwnd, ctypes.byref(wrect)):
                continue

            cw = crect.right - crect.left
            ch = crect.bottom - crect.top

            if cw <= 0 or ch <= 0:
                continue

            if prev_cw is None or prev_ch is None:
                prev_cw, prev_ch = cw, ch
                continue

            if cw != prev_cw or ch != prev_ch:
                w_changed = (cw != prev_cw)
                h_changed = (ch != prev_ch)

                if w_changed and not h_changed:
                    target_cw = cw
                    target_ch = int(round(cw * 9 / 16))
                elif h_changed and not w_changed:
                    target_ch = ch
                    target_cw = int(round(ch * 16 / 9))
                else:
                    target_cw = cw
                    target_ch = int(round(cw * 9 / 16))

                target_cw = max(640, target_cw)
                target_ch = max(360, target_ch)

                # Oran 1-2 pikselden fazla bozulduysa düzelt
                if abs(ch - target_ch) > 2 or abs(cw - target_cw) > 2:
                    border_w = (wrect.right - wrect.left) - cw
                    border_h = (wrect.bottom - wrect.top) - ch
                    new_ww = target_cw + border_w
                    new_wh = target_ch + border_h

                    user32.SetWindowPos(
                        self.chrome_hwnd, 0,
                        wrect.left, wrect.top,
                        new_ww, new_wh,
                        SWP_NOZORDER | SWP_NOACTIVATE
                    )

                    self.root.after(0, lambda: apply_borderless_region(self.chrome_hwnd, self.borderless_mode))

                prev_cw = target_cw
                prev_ch = target_ch
            else:
                prev_cw = cw
                prev_ch = ch

    # ==========================================
    # 9. KISAYOLLAR VE EYLEMLER
    # ==========================================
    def shortcut_listener(self):
        """Ctrl+Shift+T, Ctrl+Shift+R, Ctrl+Shift+B kısayollarını dinler."""
        prev_t = False
        prev_r = False
        prev_b = False

        while self.app_running:
            time.sleep(0.03)
            if not self.chrome_hwnd or not user32.IsWindow(self.chrome_hwnd):
                continue

            # Sadece video penceresi odaktayken çalışsın
            fg_hwnd = user32.GetForegroundWindow()
            if fg_hwnd != self.chrome_hwnd:
                continue

            ctrl_down = (user32.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0
            shift_down = (user32.GetAsyncKeyState(VK_SHIFT) & 0x8000) != 0

            t_down = (user32.GetAsyncKeyState(VK_T) & 0x8000) != 0
            r_down = (user32.GetAsyncKeyState(VK_R) & 0x8000) != 0
            b_down = (user32.GetAsyncKeyState(VK_B) & 0x8000) != 0

            # Ctrl+Shift+T: Her zaman üstte
            if ctrl_down and shift_down and t_down:
                if not prev_t:
                    self.root.after(0, self.toggle_always_on_top)
                    prev_t = True
            else:
                prev_t = False

            # Ctrl+Shift+R: 1280x720 ekran ortasına al
            if ctrl_down and shift_down and r_down:
                if not prev_r:
                    self.root.after(0, self.reset_window_center)
                    prev_r = True
            else:
                prev_r = False

            # Ctrl+Shift+B: Çerçevesiz mod aç/kapat
            if ctrl_down and shift_down and b_down:
                if not prev_b:
                    self.root.after(0, self.toggle_borderless)
                    prev_b = True
            else:
                prev_b = False

    def toggle_always_on_top(self):
        """Her zaman üstte modunu açar veya kapatır."""
        self.always_on_top = not self.always_on_top
        self.settings["always_on_top"] = self.always_on_top
        save_settings(self.settings)

        if self.chrome_hwnd and user32.IsWindow(self.chrome_hwnd):
            insert_after = HWND_TOPMOST if self.always_on_top else HWND_NOTOPMOST
            user32.SetWindowPos(self.chrome_hwnd, insert_after, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)

        # Buton görselini güncelle
        if self.always_on_top:
            self.pin_btn.configure(bg="#2563EB", fg="#FFFFFF")
        else:
            self.pin_btn.configure(bg="#18181b", fg="#9CA3AF")

    def reset_window_center(self):
        """Pencereyi 1280x720 istemci alanıyla ekranın ortasına getirir."""
        if self.chrome_hwnd and user32.IsWindow(self.chrome_hwnd):
            self.center_client_1280x720(self.chrome_hwnd)
            apply_borderless_region(self.chrome_hwnd, self.borderless_mode)
            self.sync_bar_now()
            self.save_window_metrics()

    def toggle_borderless(self):
        """Çerçevesiz görünümü açar veya kapatır."""
        self.borderless_mode = not self.borderless_mode
        self.settings["borderless"] = self.borderless_mode
        save_settings(self.settings)

        if self.chrome_hwnd and user32.IsWindow(self.chrome_hwnd):
            apply_borderless_region(self.chrome_hwnd, self.borderless_mode)
            if not self.borderless_mode:
                self.bar.withdraw()
                self.bar_state = "closed"

    def on_app_close(self):
        """Uygulama tamamen kapatıldığında kaynakları temizler."""
        self.app_running = False
        self.is_monitoring = False
        try:
            self.bar.destroy()
        except Exception:
            pass
        self.root.destroy()

    def run(self):
        """Ana döngüyü başlatır."""
        self.root.mainloop()

# ==========================================
# GİRİŞ NOKTASI
# ==========================================
if __name__ == "__main__":
    app = PopupVideoPlayerApp()
    app.run()
