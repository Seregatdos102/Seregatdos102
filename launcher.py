# core/browser/launcher.py
"""
🌐 LAUNCHER — запуск браузера с куками и сессией
Куки ПРАВИЛЬНО загружаются в контекст ДО создания страницы
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

from config.settings import settings
from services.logger import Logger
from core.proxy.manager import ProxyManager
from core.browser.fingerprint import Fingerprint as BrowserFingerprint
from core.browser.stealth import apply_stealth_scripts


class BrowserLauncher:
    """
    🌐 БРАУЗЕР ЛАУНЧЕР - ПРАВИЛЬНАЯ ЗАГРУЗКА КУКИ
    
    ⭐ КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ:
    - Куки загружаются в контекст ДО создания страницы
    - localStorage/sessionStorage восстанавливаются после
    - Все селекторы проверены и работают
    """
    
    def __init__(self, logger: Logger, proxy_manager: ProxyManager):
        """Инициализация"""
        
        self.logger = logger
        self.proxy_manager = proxy_manager
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self.fingerprints: Dict[str, BrowserFingerprint] = {}
        
        self.storage_dir = Path(settings.storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Инициализация Playwright"""
        if self.playwright:
            return
        
        self.playwright = await async_playwright().start()
        self.logger.system("Playwright initialized")
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # ⭐ ПРАВИЛЬНАЯ ЗАГРУЗКА КУКИ В КОНТЕКСТ (ДО создания страницы)
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def _load_cookies_to_context(
        self,
        context: BrowserContext,
        acc_id: str,
        cookies_data: list
    ) -> bool:
        """
        🔑 ЗАГРУЗИТЬ КУКИ В КОНТЕКСТ БРАУЗЕРА
        
        ⚠️ ВАЖНО: Вызывается ДО page.new_page()!
        
        Args:
            context: Контекст браузера
            acc_id: ID аккаунта
            cookies_data: Список куки из JSON
            
        Returns:
            bool: Успешно ли загружены
        """
        
        if not cookies_data:
            self.logger.warning(acc_id, "No cookies to load")
            return False
        
        try:
            valid_cookies = []
            
            for cookie in cookies_data:
                # Очищаем куки от лишних полей
                cleaned = {
                    "name": cookie.get("name"),
                    "value": cookie.get("value"),
                    "domain": cookie.get("domain"),
                    "path": cookie.get("path", "/"),
                }
                
                # Опциональные поля
                if cookie.get("expires"):
                    cleaned["expires"] = cookie.get("expires")
                
                if cookie.get("httpOnly") is not None:
                    cleaned["httpOnly"] = cookie.get("httpOnly")
                
                if cookie.get("secure") is not None:
                    cleaned["secure"] = cookie.get("secure")
                
                if cookie.get("sameSite"):
                    cleaned["sameSite"] = cookie.get("sameSite")
                
                # Проверяем обязательные поля
                if cleaned.get("name") and cleaned.get("value"):
                    valid_cookies.append(cleaned)
            
            if not valid_cookies:
                self.logger.warning(acc_id, "No valid cookies found after filtering")
                return False
            
            # ⭐ ДОБАВЛЯЕМ КУКИ В КОНТЕКСТ
            await context.add_cookies(valid_cookies)
            
            self.logger.success(
                acc_id,
                f"✅ Loaded {len(valid_cookies)} cookies to context BEFORE page creation"
            )
            
            return True
        
        except Exception as e:
            self.logger.error(acc_id, f"Failed to load cookies: {e}", severity="HIGH")
            return False
    
    async def _load_storage_state(
        self,
        page: Page,
        context: BrowserContext,
        acc_id: str
    ) -> bool:
        """
        💾 ЗАГРУЗИТЬ LOCALSTORAGE И SESSIONSTORAGE
        
        Вызывается ПОСЛЕ создания страницы
        """
        
        storage_file = self.storage_dir / f"{acc_id}_storage.json"
        
        if not storage_file.exists():
            return False
        
        try:
            with open(storage_file, 'r', encoding='utf-8') as f:
                storage_state = json.load(f)
            
            # localStorage
            if storage_state.get("origins"):
                for origin_data in storage_state["origins"]:
                    origin = origin_data.get("origin")
                    local_storage = origin_data.get("localStorage", [])
                    
                    if origin and local_storage:
                        try:
                            await page.goto(origin, wait_until="commit", timeout=5000)
                        except:
                            pass
                        
                        for item in local_storage:
                            name = item.get("name")
                            value = item.get("value")
                            
                            if name and value:
                                try:
                                    await page.evaluate(
                                        f"""
                                        try {{
                                            localStorage.setItem('{name}', '{value}');
                                        }} catch(e) {{}}
                                        """
                                    )
                                except:
                                    pass
            
            self.logger.success(acc_id, "✅ Loaded localStorage")
            return True
        
        except Exception as e:
            self.logger.warning(acc_id, f"Failed to load storage state: {e}")
            return False
    
    # ═════════════════════════════���═════════════════════════════════════════════════
    # ЗАПУСК БРАУЗЕРА - ПРАВИЛЬНЫЙ ПОРЯДОК
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def launch(self, acc_id: str) -> Optional[Page]:
        """
        🚀 ЗАПУСТИТЬ БРАУЗЕР С КУКАМИ
        
        ⭐ ПРАВИЛЬНЫЙ ПОРЯДОК:
        1. Инициализация Playwright
        2. Запуск браузера
        3. Создание контекста
        4. ✅ ЗАГРУЗКА КУКИ В КОНТЕКСТ (ДО создания страницы!)
        5. Создание страницы
        6. Применение Stealth
        7. Восстановление localStorage
        8. Возвращаем готовую страницу с работающей сессией
        """
        
        if not self.playwright:
            await self.initialize()
        
        try:
            account_config = settings.accounts.get(acc_id)
            if not account_config:
                self.logger.error(acc_id, "Account config not found", severity="CRITICAL")
                return None
            
            phone = account_config.get("phone", "unknown")
            
            # ─────────────────────────────────────────────────────
            # 1. ЗАПУСК БРАУЗЕРА
            # ─────────────────────────────────────────────────────
            
            if not self.browser:
                launch_args = {
                    "headless": settings.headless,
                    "args": [
                        "--disable-blink-features=AutomationControlled",
                        "--disable-features=IsolateOrigins,site-per-process",
                        "--disable-popup-blocking",
                        "--disable-prompt-on-repost",
                        "--disable-hang-monitor",
                        "--disable-sync",
                        "--disable-web-resources",
                        "--no-first-run",
                        "--no-default-browser-check",
                    ],
                }
                
                # ⭐⭐⭐ ИСПРАВЛЕННАЯ СТРОКА (151) ⭐⭐⭐
                proxy_config = self.proxy_manager.get_playwright_proxy(acc_id)
                if proxy_config:
                    launch_args["proxy"] = proxy_config
                
                self.browser = await self.playwright.chromium.launch(**launch_args)
                self.logger.system(f"🟢 Browser launched (headless={settings.headless})")
            
            # ─────────────────────────────────────────────────────
            # 2. ЗАГРУЖАЕМ КУКИ ИЗ ФАЙЛА
            # ─────────────────────────────────────────────────────
            
            cookies_data = []
            cookies_file = self.storage_dir / f"{acc_id}.json"
            
            if cookies_file.exists():
                try:
                    with open(cookies_file, 'r', encoding='utf-8') as f:
                        cookies_data = json.load(f)
                    self.logger.info(acc_id, f"✅ Loaded {len(cookies_data)} cookies from file")
                except Exception as e:
                    self.logger.warning(acc_id, f"Failed to read cookies file: {e}")
            else:
                self.logger.warning(acc_id, f"Cookies file not found: {cookies_file}")
            
            # ─────────────────────────────────────────────────────
            # 3. СОЗДАЕМ КОНТЕКСТ (с куками!)
            # ─────────────────────────────────────────────────────
            
            fingerprint = BrowserFingerprint()
            self.fingerprints[acc_id] = fingerprint
            
            context_options = {
                "viewport": fingerprint.viewport,
                "user_agent": fingerprint.user_agent,
                "locale": "ru-RU",
                "timezone_id": fingerprint.timezone,
                "geolocation": fingerprint.geolocation,
                "permissions": ["geolocation"],
                "extra_http_headers": {
                    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                },
            }
            
            context = await self.browser.new_context(**context_options)
            
            # ⭐⭐⭐ ЗАГРУЖАЕМ КУКИ В КОНТЕКСТ ДО СОЗДАНИЯ СТРАНИЦЫ ⭐⭐⭐
            cookies_loaded = await self._load_cookies_to_context(context, acc_id, cookies_data)
            
            self.contexts[acc_id] = context
            
            # ─────────────────────────────────────────────────────
            # 4. СОЗДАЕМ СТРАНИЦУ (уже с куками в контексте!)
            # ─────────────────────────────────────────────────────
            
            page = await context.new_page()
            
            # Применяем Stealth
            await apply_stealth_scripts(page)
            
            # ────────────��────────────────────────────────────────
            # 5. ВОССТАНАВЛИВАЕМ LOCALSTORAGE (если нужно)
            # ─────────────────────────────────────────────────────
            
            await self._load_storage_state(page, context, acc_id)
            
            self.pages[acc_id] = page
            
            status_msg = "✅ with saved cookies" if cookies_loaded else "🆕 without cookies"
            
            self.logger.success(
                acc_id,
                f"🟢 Browser launched {status_msg} ({phone})"
            )
            
            return page
        
        except Exception as e:
            self.logger.error(
                acc_id,
                f"❌ Failed to launch browser: {e}",
                severity="CRITICAL"
            )
            return None
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # СОХРАНЕНИЕ КУКИ ПОСЛЕ ДЕЙСТВИЙ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def save_cookies(self, acc_id: str) -> bool:
        """
        💾 СОХРАНИТЬ КУКИ ИЗ БРАУЗЕРА
        
        Вызывайте ЭТО после успешного входа или важных действий!
        """
        
        if acc_id not in self.contexts:
            self.logger.warning(acc_id, "Context not found for saving cookies")
            return False
        
        try:
            context = self.contexts[acc_id]
            cookies = await context.cookies()
            
            if not cookies:
                self.logger.warning(acc_id, "No cookies to save")
                return False
            
            cookies_file = self.storage_dir / f"{acc_id}.json"
            
            with open(cookies_file, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            self.logger.success(acc_id, f"💾 Saved {len(cookies)} cookies")
            
            return True
        
        except Exception as e:
            self.logger.error(acc_id, f"Failed to save cookies: {e}", severity="HIGH")
            return False
    
    async def save_storage_state(self, acc_id: str) -> bool:
        """💾 СОХРАНИТЬ LOCALSTORAGE"""
        
        if acc_id not in self.pages:
            return False
        
        try:
            context = self.contexts[acc_id]
            storage_state = await context.storage_state()
            
            storage_file = self.storage_dir / f"{acc_id}_storage.json"
            
            with open(storage_file, 'w', encoding='utf-8') as f:
                json.dump(storage_state, f, indent=2, ensure_ascii=False)
            
            self.logger.success(acc_id, "💾 Saved storage state")
            return True
        
        except Exception as e:
            self.logger.warning(acc_id, f"Failed to save storage state: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # УПРАВЛЕНИЕ
    # ═══════════════════════════════════════════════════════════════════════════════
    
    async def close(self, acc_id: str):
        """Закрыть браузер (куки сохранены)"""
        
        try:
            await self.save_cookies(acc_id)
            await self.save_storage_state(acc_id)
            
            if acc_id in self.pages:
                await self.pages[acc_id].close()
                del self.pages[acc_id]
            
            if acc_id in self.contexts:
                await self.contexts[acc_id].close()
                del self.contexts[acc_id]
            
            self.logger.success(acc_id, "✅ Browser closed (cookies saved)")
        
        except Exception as e:
            self.logger.error(acc_id, f"Error closing browser: {e}")
    
    async def close_all(self):
        """Закрыть все браузеры"""
        
        for acc_id in list(self.pages.keys()):
            await self.close(acc_id)
        
        if self.browser:
            await self.browser.close()
            self.logger.system("🟡 All browsers closed")
    
    async def reset_session(self, acc_id: str):
        """Полный сброс сессии"""
        
        cookies_file = self.storage_dir / f"{acc_id}.json"
        storage_file = self.storage_dir / f"{acc_id}_storage.json"
        
        try:
            if cookies_file.exists():
                cookies_file.unlink()
            if storage_file.exists():
                storage_file.unlink()
            
            await self.close(acc_id)
            
            self.logger.success(acc_id, "✅ Session reset (cookies deleted)")
        
        except Exception as e:
            self.logger.error(acc_id, f"Error resetting session: {e}")
    
    def get_fingerprint(self, acc_id: str) -> Optional[BrowserFingerprint]:
        """Получить fingerprint"""
        return self.fingerprints.get(acc_id)
    
    def get_page(self, acc_id: str) -> Optional[Page]:
        """Получить страницу"""
        return self.pages.get(acc_id)