# core/avito/login.py
"""
🔐 LOGIN — вход на Avito с правильным сохранением куки
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from playwright.async_api import Page
    from core.avito.navigator import AvitoNavigator
    from services.logger import Logger
    from services.notifier import TelegramNotifier
    from core.browser.launcher import BrowserLauncher


async def login_with_session(
    page: Page,
    acc_id: str,
    navigator: AvitoNavigator,
    logger: Logger
) -> bool:
    """
    🔑 ВХОД С СОХРАНЁННОЙ СЕССИЕЙ
    Куки уже загружены в контекст браузера!
    """
    
    try:
        logger.info(acc_id, "Checking saved session...")
        
        # Переходим на главную
        await navigator.goto_main(page)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        # Проверяем авторизацию
        is_auth = await page.evaluate("""
            () => {
                // Проверяем несколько признаков авторизации
                const profile = document.querySelector('[data-marker="account-menu-button"]');
                const userLink = document.querySelector('a[href*="/user/"]');
                return !!(profile || userLink);
            }
        """)
        
        if is_auth:
            logger.success(acc_id, "✅ Session check: AUTHENTICATED")
            return True
        else:
            logger.warning(acc_id, "Session check: NOT AUTHENTICATED")
            return False
    
    except Exception as e:
        logger.warning(acc_id, f"Session check failed: {e}")
        return False


async def login_with_sms(
    page: Page,
    acc_id: str,
    phone: str,
    navigator: AvitoNavigator,
    logger: Logger,
    notifier: Optional[TelegramNotifier],
    fingerprint,
    launcher: Optional[BrowserLauncher] = None
) -> bool:
    """
    📱 ВХОД ЧЕРЕЗ SMS
    
    После успешного входа ⭐ СОХРАНЯЕМ КУКИ!
    """
    
    try:
        logger.info(acc_id, f"🔐 Starting SMS login for {phone}")
        
        # ─────────────────────────────────────────────────────
        # 1. ПЕРЕХОДИМ НА LOGIN
        # ─────────────────────────────────────────────────────
        
        await navigator.goto_login(page)
        await page.wait_for_load_state("networkidle", timeout=10000)
        
        logger.info(acc_id, "On login page")
        
        # ─────────────────────────────────────────────────────
        # 2. ВВОДИМ НОМЕР
        # ─────────────────────────────────────────────────────
        
        logger.info(acc_id, f"Entering phone: {phone}")
        
        phone_input = await page.query_selector('input[type="tel"]')
        if phone_input:
            await phone_input.fill(phone)
            await page.wait_for_timeout(500)
            
            continue_btn = await page.query_selector('button[type="submit"]')
            if continue_btn:
                await continue_btn.click()
                await page.wait_for_timeout(2000)
        
        logger.info(acc_id, "Waiting for SMS code...")
        
        # ─────────────────────────────────────────────────────
        # 3. ЖДЁМ СМС КОДА
        # ─────────────────────────────────────────────────────
        
        logger.warning(acc_id, "🔔 WAITING FOR SMS CODE")
        
        if notifier:
            try:
                await notifier.notify_sms_needed(acc_id, phone)
            except:
                pass
        
        sms_code = None
        max_attempts = 300  # 5 минут
        
        for attempt in range(max_attempts):
            code_input = await page.query_selector('input[inputmode="numeric"]')
            
            if code_input:
                code_value = await code_input.input_value()
                if code_value and len(code_value) == 4:
                    sms_code = code_value
                    logger.success(acc_id, f"✅ SMS code received: {sms_code}")
                    break
            
            await page.wait_for_timeout(1000)
        
        if not sms_code:
            logger.error(acc_id, "❌ SMS code timeout", severity="HIGH")
            return False
        
        # ─────────────────────────────────────────────────────
        # 4. ПРОВЕРЯЕМ АВТОРИЗАЦИЮ
        # ─────────────────────────────────────────────────────
        
        await page.wait_for_load_state("networkidle", timeout=10000)
        await page.wait_for_timeout(3000)
        
        is_auth = await page.evaluate("""
            () => {
                const profile = document.querySelector('[data-marker="account-menu-button"]');
                const userLink = document.querySelector('a[href*="/user/"]');
                return !!(profile || userLink);
            }
        """)
        
        if not is_auth:
            logger.error(acc_id, "Login verification failed", severity="HIGH")
            return False
        
        logger.success(acc_id, "✅ AUTHENTICATED VIA SMS")
        
        # ─────────────────────────────────────────────────────
        # 5. ⭐⭐⭐ СОХРАНЯЕМ КУКИ
        # ─────────────────────────────────────────────────────
        
        if launcher:
            logger.info(acc_id, "Saving cookies and storage...")
            
            await launcher.save_cookies(acc_id)
            await launcher.save_storage_state(acc_id)
            
            logger.success(acc_id, "✅ Cookies saved for future logins")
        
        if notifier:
            try:
                await notifier.notify_login_success(acc_id, phone, "sms")
            except:
                pass
        
        return True
    
    except Exception as e:
        logger.error(acc_id, f"SMS login failed: {e}", severity="HIGH")
        
        if notifier:
            try:
                await notifier.notify_login_failed(acc_id, phone)
            except:
                pass
        
        return False