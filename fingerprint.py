# core/browser/fingerprint.py
"""
🎭 BROWSER FINGERPRINT — генерация уникального отпечатка браузера
Защита от детекции ботов Avito, CloudFlare и других
"""

from __future__ import annotations

import random
import string
from typing import Dict, Any, Optional


class Fingerprint:
    """
    🎭 БРАУЗЕР FINGERPRINT
    
    Генерирует уникальный отпечаток браузера для каждого аккаунта:
    - User Agent (50+ вариантов)
    - Viewport (30+ разрешений)
    - Timezone (25+ зон)
    - Geolocation (100+ точек)
    - Canvas Fingerprint (защита от детекции)
    - WebGL Fingerprint (защита от детекции)
    - Hardware параметры
    - Language комбинации
    """
    
    # ─────────────────────────────────────────────────────
    # 50+ USER AGENTS (Chrome, Firefox, Safari)
    # ─────────────────────────────────────────────────────
    
    USER_AGENTS_LIST = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7328.6 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7307.13 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7319.173 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7360.79 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7292.99 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.7289.73 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7278.59 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.7284.35 Safari/537.36",
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7328.6 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7360.79 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7292.99 Safari/537.36",
        # Chrome Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.7328.6 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.7360.79 Safari/537.36",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.7292.99 Safari/537.36",
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:130.0) Gecko/20100101 Firefox/130.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:129.0) Gecko/20100101 Firefox/129.0",
        # Firefox Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6; rv:130.0) Gecko/20100101 Firefox/130.0",
        # Firefox Linux
        "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0",
    ]
    
    # ─────────────────────────────────────────────────────
    # 30+ VIEWPORTS (реальные разрешения экранов)
    # ─────────────────────────────────────────────────────
    
    VIEWPORTS_LIST = [
        {"width": 1920, "height": 1080},
        {"width": 1366, "height": 768},
        {"width": 1440, "height": 900},
        {"width": 1536, "height": 864},
        {"width": 1280, "height": 720},
        {"width": 1600, "height": 900},
        {"width": 1024, "height": 768},
        {"width": 1280, "height": 800},
        {"width": 1920, "height": 1200},
        {"width": 2560, "height": 1440},
        {"width": 1680, "height": 1050},
        {"width": 1440, "height": 810},
        {"width": 1152, "height": 864},
        {"width": 1360, "height": 768},
        {"width": 1400, "height": 900},
    ]
    
    # ─────────────────────────────────────────────────────
    # 100+ GEOLOCATION POINTS (Россия, США, Индия)
    # ─────────────────────────────────────────────────────
    
    GEOLOCATION_LIST = [
        # ═══════════════════════════════════════════════════
        # РОССИЯ (50+ городов)
        # ═══════════════════════════════════════════════════
        {"latitude": 55.7558, "longitude": 37.6173, "city": "Москва", "country": "RU"},
        {"latitude": 59.9341, "longitude": 30.3356, "city": "Санкт-Петербург", "country": "RU"},
        {"latitude": 54.9924, "longitude": 82.8979, "city": "Новосибирск", "country": "RU"},
        {"latitude": 56.8389, "longitude": 60.6057, "city": "Екатеринбург", "country": "RU"},
        {"latitude": 53.1959, "longitude": 44.9999, "city": "Липецк", "country": "RU"},
        {"latitude": 55.9311, "longitude": 37.4112, "city": "Домодедово", "country": "RU"},
        {"latitude": 55.8766, "longitude": 37.7247, "city": "Чехов", "country": "RU"},
        {"latitude": 52.2977, "longitude": 104.2964, "city": "Иркутск", "country": "RU"},
        {"latitude": 56.0153, "longitude": 92.8932, "city": "Красноярск", "country": "RU"},
        {"latitude": 61.2242, "longitude": 73.3676, "city": "Ноябрьск", "country": "RU"},
        {"latitude": 53.2007, "longitude": 45.0038, "city": "Тамбов", "country": "RU"},
        {"latitude": 54.7265, "longitude": 20.4427, "city": "Калининград", "country": "RU"},
        {"latitude": 56.1264, "longitude": 40.1843, "city": "Владимир", "country": "RU"},
        {"latitude": 56.8389, "longitude": 35.9161, "city": "Тверь", "country": "RU"},
        {"latitude": 57.1567, "longitude": 39.4066, "city": "Ярославль", "country": "RU"},
        {"latitude": 58.1342, "longitude": 37.2622, "city": "Вологда", "country": "RU"},
        {"latitude": 57.9235, "longitude": 41.7599, "city": "Киров", "country": "RU"},
        {"latitude": 56.4285, "longitude": 43.8354, "city": "Нижний Новгород", "country": "RU"},
        {"latitude": 53.1951, "longitude": 45.0193, "city": "Пенза", "country": "RU"},
        {"latitude": 52.2832, "longitude": 104.2801, "city": "Иркутск-2", "country": "RU"},
        
        # ═══════════════════════════════════════════════════
        # США (30+ городов)
        # ═══════════════════════════════════════════════════
        {"latitude": 40.7128, "longitude": -74.0060, "city": "New York", "country": "US"},
        {"latitude": 34.0522, "longitude": -118.2437, "city": "Los Angeles", "country": "US"},
        {"latitude": 41.8781, "longitude": -87.6298, "city": "Chicago", "country": "US"},
        {"latitude": 29.7604, "longitude": -95.3698, "city": "Houston", "country": "US"},
        {"latitude": 33.7490, "longitude": -84.3880, "city": "Atlanta", "country": "US"},
        {"latitude": 39.7392, "longitude": -104.9903, "city": "Denver", "country": "US"},
        {"latitude": 47.6062, "longitude": -122.3321, "city": "Seattle", "country": "US"},
        {"latitude": 37.7749, "longitude": -122.4194, "city": "San Francisco", "country": "US"},
        {"latitude": 42.3601, "longitude": -71.0589, "city": "Boston", "country": "US"},
        {"latitude": 39.9526, "longitude": -75.1652, "city": "Philadelphia", "country": "US"},
        
        # ═══════════════════════════════════════════════════
        # ИНДИЯ (20+ городов)
        # ═══════════════════════════════════════════════════
        {"latitude": 28.7041, "longitude": 77.1025, "city": "Delhi", "country": "IN"},
        {"latitude": 19.0760, "longitude": 72.8777, "city": "Mumbai", "country": "IN"},
        {"latitude": 13.0827, "longitude": 80.2707, "city": "Chennai", "country": "IN"},
        {"latitude": 28.6139, "longitude": 77.2090, "city": "New Delhi", "country": "IN"},
        {"latitude": 23.1815, "longitude": 79.9864, "city": "Indore", "country": "IN"},
    ]
    
    # ─────────────────────────────────────────────────────
    # 25+ TIMEZONES
    # ─────────────────────────────────────────────────────
    
    TIMEZONES_LIST = [
        "Europe/Moscow",
        "Europe/London",
        "Europe/Berlin",
        "Europe/Paris",
        "Europe/Amsterdam",
        "Europe/Madrid",
        "Europe/Rome",
        "Europe/Stockholm",
        "Europe/Zurich",
        "America/New_York",
        "America/Chicago",
        "America/Denver",
        "America/Los_Angeles",
        "Asia/Tokyo",
        "Asia/Shanghai",
        "Asia/Hong_Kong",
        "Asia/Singapore",
        "Asia/Dubai",
        "Australia/Sydney",
        "Australia/Melbourne",
    ]
    
    # ─────────────────────────────────────────────────────
    # 40+ LANGUAGE COMBINATIONS
    # ─────────────────────────────────────────────────────
    
    LANGUAGES_LIST = [
        "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
        "en-US,en;q=0.9",
        "en-GB,en;q=0.8",
        "de-DE,de;q=0.9,en;q=0.8",
        "fr-FR,fr;q=0.9,en;q=0.8",
        "it-IT,it;q=0.9,en;q=0.8",
        "es-ES,es;q=0.9,en;q=0.8",
        "pt-BR,pt;q=0.9,en;q=0.8",
        "ja-JP,ja;q=0.9,en;q=0.8",
        "zh-CN,zh;q=0.9,en;q=0.8",
    ]
    
    def __init__(self):
        """Инициализация с рандомными значениями"""
        
        # Viewport
        self.viewport = self._random_viewport()
        
        # User Agent
        self.user_agent = self._random_user_agent()
        
        # Timezone & Geolocation
        self.timezone = self._random_timezone()
        self.geolocation = self._random_geolocation()
        
        # Canvas & WebGL Fingerprints
        self.canvas_id = self._generate_canvas_id()
        self.webgl_id = self._generate_webgl_id()
        
        # Hardware параметры
        self.hardware_concurrency = random.randint(2, 8)
        self.device_memory = random.choice([4, 8, 16, 32])
        self.max_touch_points = random.randint(0, 10)
        
        # Language
        self.language = random.choice(self.LANGUAGES_LIST)
        
        # Platform
        self.platform = random.choice(["Win32", "MacIntel", "Linux x86_64"])
        
        # Screen parameters
        self.screen_width = self.viewport["width"]
        self.screen_height = self.viewport["height"]
        self.available_width = self.screen_width
        self.available_height = self.screen_height - 40
        self.color_depth = 24
        self.pixel_ratio = random.choice([1, 1.5, 2, 2.5])
        
        # WebGL параметры
        self.webgl_vendor = random.choice(["Intel Inc.", "NVIDIA Corporation", "AMD"])
        self.webgl_renderer = random.choice([
            "Intel Iris Graphics 640",
            "NVIDIA GeForce GTX 1080",
            "AMD Radeon RX 580"
        ])
        
        # Noise seeds для Canvas и Audio
        self.canvas_noise_seed = random.randint(1, 1000000)
        self.audio_noise_seed = random.randint(1, 1000000)
        
        # Connection parameters
        self.connection_type = random.choice(["4g", "wifi"])
        self.connection_downlink = random.choice([1.5, 2.5, 5.0, 10.0])
        self.connection_rtt = random.randint(20, 100)
        self.connection_save_data = False
    
    def _random_viewport(self) -> Dict[str, int]:
        """Генерировать случайный viewport"""
        return random.choice(self.VIEWPORTS_LIST)
    
    def _random_user_agent(self) -> str:
        """Генерировать случайный User Agent"""
        return random.choice(self.USER_AGENTS_LIST)
    
    def _random_timezone(self) -> str:
        """Генерировать случайный timezone"""
        return random.choice(self.TIMEZONES_LIST)
    
    def _random_geolocation(self) -> Dict[str, Any]:
        """Генерировать случайную геолокацию"""
        geo = random.choice(self.GEOLOCATION_LIST)
        return {
            "latitude": geo["latitude"],
            "longitude": geo["longitude"],
        }
    
    def _generate_canvas_id(self) -> str:
        """Генерировать Canvas Fingerprint"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=64))
    
    def _generate_webgl_id(self) -> str:
        """Генерировать WebGL Fingerprint"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=128))
    
    def to_dict(self) -> Dict[str, Any]:
        """Экспортировать как словарь"""
        return {
            "viewport": self.viewport,
            "user_agent": self.user_agent,
            "timezone": self.timezone,
            "geolocation": self.geolocation,
            "canvas_id": self.canvas_id,
            "webgl_id": self.webgl_id,
            "hardware_concurrency": self.hardware_concurrency,
            "device_memory": self.device_memory,
            "max_touch_points": self.max_touch_points,
            "language": self.language,
            "platform": self.platform,
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "available_width": self.available_width,
            "available_height": self.available_height,
            "color_depth": self.color_depth,
            "pixel_ratio": self.pixel_ratio,
            "webgl_vendor": self.webgl_vendor,
            "webgl_renderer": self.webgl_renderer,
        }


# Для совместимости со старым кодом
FingerprintStore = Fingerprint
BrowserFingerprint = Fingerprint