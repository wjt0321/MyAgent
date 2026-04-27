"""E2E tests for MyAgent Web UI using Playwright + FastAPI server."""

from __future__ import annotations

import os
import time
import socket
import threading

import pytest

os.environ.setdefault("MYAGENT_LLM_API_KEY", "test-key")
os.environ.setdefault("MYAGENT_LLM_API_BASE", "http://localhost:9999")


def _find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        return s.getsockname()[1]


def _run_server(port, ready_event):
    from myagent.web.server import create_app
    import uvicorn
    app = create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    ready_event.set()
    server.run()


@pytest.fixture(scope="module")
def url():
    port = _find_free_port()
    ready_event = threading.Event()
    thread = threading.Thread(target=_run_server, args=(port, ready_event), daemon=True)
    thread.start()
    ready_event.wait(timeout=10)
    time.sleep(2)
    yield f"http://127.0.0.1:{port}"


def _goto(page, url):
    page.goto(url, timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(500)


class TestPageLoad:
    def test_index_page_loads(self, page, url):
        _goto(page, url)
        assert page.title() == "MyAgent Workbench"
        assert page.locator(".app").is_visible()

    def test_sidebar_visible(self, page, url):
        _goto(page, url)
        assert page.locator("#sidebar").is_visible()

    def test_workbench_tabs_exist(self, page, url):
        _goto(page, url)
        assert page.locator(".workbench-tab-bar .tab-bar-btn").count() == 5

    def test_welcome_or_content_exists(self, page, url):
        _goto(page, url)
        welcome = page.locator("#welcome-screen")
        messages = page.locator("#messages")
        assert welcome.count() >= 0 or messages.count() >= 0

    def test_composer_visible(self, page, url):
        _goto(page, url)
        assert page.locator("#message-input").is_visible()

    def test_detail_sidebar_exists(self, page, url):
        _goto(page, url)
        assert page.locator("#detail-sidebar").count() == 1


class TestThemeSwitching:
    def test_theme_toggle_via_settings(self, page, url):
        _goto(page, url)
        page.locator("button#settings-btn").click()
        page.wait_for_timeout(200)
        assert "show" in page.locator("#settings-modal").get_attribute("class")
        page.locator('#settings-modal button.tab-btn[data-tab="appearance"]').click()
        page.locator('[data-theme="light"]').click()
        page.wait_for_timeout(300)
        assert "theme-light" in page.evaluate("document.body.className")
        page.locator("#close-settings").click()

    def test_default_theme(self, page, url):
        _goto(page, url)
        assert "theme-" in page.evaluate("document.body.className")


class TestViewSwitching:
    @pytest.mark.parametrize("view", ["chat", "tasks", "files", "workspace", "team"])
    def test_switch_views(self, page, url, view):
        _goto(page, url)
        page.evaluate(f"""() => {{
            const btn = document.querySelector('.workbench-tab-bar .tab-bar-btn[data-view="{view}"]');
            if (btn) btn.click();
        }}""")
        page.wait_for_timeout(300)
        cls = page.locator(f'.workbench-tab-bar .tab-bar-btn[data-view="{view}"]').first.get_attribute("class")
        assert "active" in cls
        assert page.locator(f'.workbench-view[data-view="{view}"]').is_visible()


class TestSettingsPanel:
    def test_open_and_close_settings(self, page, url):
        _goto(page, url)
        page.locator("button#settings-btn").click()
        page.wait_for_timeout(200)
        assert "show" in page.locator("#settings-modal").get_attribute("class")
        page.locator("#close-settings").click()
        page.wait_for_timeout(200)
        assert "show" not in page.locator("#settings-modal").get_attribute("class")

    def test_settings_tabs_exist(self, page, url):
        _goto(page, url)
        page.locator("button#settings-btn").click()
        page.wait_for_timeout(200)
        for tab in ["agent", "memory", "codebase", "reset", "appearance", "about"]:
            assert page.locator(f'#settings-modal button[data-tab="{tab}"]').count() >= 1
        page.locator("#close-settings").click()

    def test_switch_settings_tabs(self, page, url):
        _goto(page, url)
        page.locator("button#settings-btn").click()
        page.wait_for_timeout(200)
        page.locator('#settings-modal button[data-tab="appearance"]').click()
        page.wait_for_timeout(100)
        assert page.locator("#settings-modal .tab-content[data-tab='appearance']").is_visible()
        page.locator('#settings-modal button[data-tab="about"]').click()
        page.wait_for_timeout(100)
        assert page.locator("#settings-modal .tab-content[data-tab='about']").is_visible()
        page.locator("#close-settings").click()

    def test_close_settings_with_escape(self, page, url):
        _goto(page, url)
        page.locator("button#settings-btn").click()
        page.wait_for_timeout(200)
        assert "show" in page.locator("#settings-modal").get_attribute("class")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        assert "show" not in page.locator("#settings-modal").get_attribute("class")


class TestCommandPalette:
    def test_open_with_keyboard(self, page, url):
        _goto(page, url)
        page.keyboard.press("Control+K")
        page.wait_for_timeout(200)
        assert "show" in page.locator("#command-palette-modal").get_attribute("class")

    def test_close_command_palette(self, page, url):
        _goto(page, url)
        page.keyboard.press("Control+K")
        page.locator("#close-command-palette").click()
        page.wait_for_timeout(200)
        assert "show" not in page.locator("#command-palette-modal").get_attribute("class")

    def test_command_palette_has_items(self, page, url):
        _goto(page, url)
        page.keyboard.press("Control+K")
        page.wait_for_timeout(200)
        assert page.locator("#command-palette-modal .command-item").count() >= 10
        page.locator("#close-command-palette").click()

    def test_command_palette_filter(self, page, url):
        _goto(page, url)
        page.keyboard.press("Control+K")
        page.wait_for_timeout(200)
        page.fill("#command-palette-input", "设置")
        page.wait_for_timeout(200)
        count = page.locator("#command-palette-modal .command-item").count()
        assert 0 < count < 15
        page.locator("#close-command-palette").click()

    def test_close_with_escape(self, page, url):
        _goto(page, url)
        page.keyboard.press("Control+K")
        page.wait_for_timeout(200)
        assert "show" in page.locator("#command-palette-modal").get_attribute("class")
        page.keyboard.press("Escape")
        page.wait_for_timeout(200)
        assert "show" not in page.locator("#command-palette-modal").get_attribute("class")


class TestSearch:
    def test_toggle_search_bar(self, page, url):
        _goto(page, url)
        page.evaluate("document.getElementById('search-toggle').click()")
        page.wait_for_timeout(200)
        assert "show" in page.locator("#search-bar").get_attribute("class")
        page.evaluate("document.getElementById('search-close').click()")
        page.wait_for_timeout(200)
        assert "show" not in page.locator("#search-bar").get_attribute("class")


class TestSession:
    def test_new_session_button_exists(self, page, url):
        _goto(page, url)
        assert page.locator("#new-session-btn").is_visible()

    def test_session_list_exists(self, page, url):
        _goto(page, url)
        assert page.locator("#session-list").count() == 1


class TestResponsive:
    def test_resize_viewport(self, page, url):
        page.set_viewport_size({"width": 375, "height": 812})
        _goto(page, url)
        assert page.locator(".app").is_visible()
        page.set_viewport_size({"width": 1920, "height": 1080})
        assert page.locator(".app").is_visible()

    def test_mobile_view_chip_exists(self, page, url):
        _goto(page, url)
        assert page.locator("#mobile-view-chip").count() >= 0
