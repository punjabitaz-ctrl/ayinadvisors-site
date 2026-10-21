"""Light/dark switch behaviour in real Chromium: no flash, storage failure, system changes, toggle semantics."""
import pytest

from a11y_browser.conftest import new_context, open_page

pytestmark = pytest.mark.browser

RECORD = """
window.__themeAtDCL = null; window.__themeSeen = [];
new MutationObserver(() => { const t = document.documentElement.dataset.theme; if (t && window.__themeSeen[window.__themeSeen.length-1] !== t) window.__themeSeen.push(t); })
  .observe(document, {attributes: true, subtree: true, attributeFilter: ['data-theme']});
document.addEventListener('DOMContentLoaded', () => { window.__themeAtDCL = document.documentElement.dataset.theme || null; });
"""
BLOCK_STORAGE = "Object.defineProperty(window, 'localStorage', {get() { throw new Error('storage blocked'); }});"
THEME = "document.documentElement.dataset.theme"
PRESSED = "[...document.querySelectorAll('.theme-toggle')].map(b => b.getAttribute('aria-pressed'))"
SURFACE = "getComputedStyle(document.documentElement).getPropertyValue('--surface').trim()"


def _ctx(browser, width=1280, scheme="light", stored=None, **kw):
    ctx = new_context(browser, width, 900, color_scheme=scheme, **kw)
    if stored:
        ctx.add_init_script(f"try {{ localStorage.setItem('ayin-theme', '{stored}'); }} catch (e) {{}}")
    ctx.add_init_script(RECORD)
    return ctx


@pytest.mark.parametrize("stored,system", [("light", "dark"), ("dark", "light")])
def test_no_flash_stored_choice_beats_system(browser, site_url, stored, system):
    ctx = _ctx(browser, scheme=system, stored=stored)
    page = open_page(ctx, site_url, "index")
    assert page.evaluate("window.__themeAtDCL") == stored
    assert page.evaluate("window.__themeSeen") == [stored]  # set once, never corrected later
    assert page.evaluate(SURFACE) == ("#061325" if stored == "dark" else "#faf7f0")
    ctx.close()


def test_follows_system_when_no_choice_and_live_changes(browser, site_url):
    ctx = _ctx(browser, scheme="light")
    page = open_page(ctx, site_url, "index")
    assert page.evaluate(THEME) == "light"
    page.emulate_media(color_scheme="dark")
    page.wait_for_function(f"{THEME} === 'dark'")
    assert page.evaluate("localStorage.getItem('ayin-theme')") is None  # following is not choosing
    assert page.locator(".nav .theme-toggle").get_attribute("aria-pressed") == "true"
    page.emulate_media(color_scheme="light")
    page.wait_for_function(f"{THEME} === 'light'")
    ctx.close()


def test_stored_choice_not_overridden_by_system_change(browser, site_url):
    ctx = _ctx(browser, scheme="light", stored="light")
    page = open_page(ctx, site_url, "index")
    page.emulate_media(color_scheme="dark")
    page.wait_for_timeout(300)
    assert page.evaluate(THEME) == "light"
    ctx.close()


def test_choice_persists_across_reload(browser, site_url):
    ctx = _ctx(browser, scheme="light")
    page = open_page(ctx, site_url, "index")
    page.locator(".nav .theme-toggle").click()
    assert page.evaluate("localStorage.getItem('ayin-theme')") == "dark"
    page.reload()
    assert page.evaluate("window.__themeAtDCL") == "dark"
    ctx.close()


def test_storage_blocked_still_toggles(browser, site_url):
    ctx = new_context(browser, 1280, 900, color_scheme="light")
    ctx.add_init_script(BLOCK_STORAGE)
    errors = []
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{site_url}/index.html", wait_until="load")
    assert page.evaluate(THEME) == "light"  # system theme
    page.locator(".nav .theme-toggle").click()
    assert page.evaluate(THEME) == "dark"
    page.locator(".nav .theme-toggle").click()
    assert page.evaluate(THEME) == "light"
    assert not errors, errors
    ctx.close()


def test_toggle_semantics(browser, site_url):
    ctx = _ctx(browser, scheme="light")
    page = open_page(ctx, site_url, "index")
    btn = page.get_by_role("button", name="Dark mode", exact=True)
    assert btn.count() == 1  # the drawer copy is hidden while closed
    assert btn.get_attribute("aria-pressed") == "false"
    btn.focus()
    page.keyboard.press("Enter")
    assert page.evaluate(THEME) == "dark"
    assert btn.get_attribute("aria-pressed") == "true"
    assert page.evaluate("document.activeElement.classList.contains('theme-toggle')")
    assert page.evaluate(PRESSED) == ["true", "true"]  # nav and drawer in sync
    page.keyboard.press("Space")
    assert page.evaluate(THEME) == "light"
    assert page.evaluate(PRESSED) == ["false", "false"]
    assert btn.get_attribute("aria-label") == "Dark mode"
    ctx.close()


def test_themechange_event_and_meta_theme_color(browser, site_url):
    ctx = _ctx(browser, scheme="light")
    page = open_page(ctx, site_url, "index")
    page.evaluate("window.__tc = []; window.addEventListener('themechange', e => window.__tc.push(e.detail && e.detail.theme));")
    before = page.evaluate("document.querySelector('meta[name=theme-color]').content")
    page.locator(".nav .theme-toggle").click()
    assert page.evaluate("window.__tc") == ["dark"]
    assert page.evaluate("document.querySelector('meta[name=theme-color]').content") == before  # navy in both themes
    ctx.close()


def test_drawer_toggle_in_sync_on_mobile(browser, site_url):
    ctx = _ctx(browser, 375, scheme="light")
    page = open_page(ctx, site_url, "index")
    page.locator(".nav-toggle").click()
    drawer_btn = page.locator(".mobile-drawer .theme-toggle")
    drawer_btn.wait_for(state="visible")
    drawer_btn.click()
    assert page.evaluate(THEME) == "dark"
    assert page.locator(".nav .theme-toggle").get_attribute("aria-pressed") == "true"
    assert page.evaluate("document.activeElement.closest('.mobile-drawer') !== null")
    ctx.close()


def test_toggle_hidden_without_js(browser, site_url):
    ctx = new_context(browser, 1280, 900, color_scheme="dark", java_script_enabled=False)
    page = open_page(ctx, site_url, "index")
    assert not page.locator(".nav .theme-toggle").is_visible()
    # system dark still applies through the :root:not([data-theme]) media rules
    assert page.evaluate(SURFACE) == "#061325"
    assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == "dark"
    ctx.close()


def test_explicit_light_beats_dark_system(browser, site_url):
    ctx = _ctx(browser, scheme="dark", stored="light")
    page = open_page(ctx, site_url, "index")
    assert page.evaluate(SURFACE) == "#faf7f0"
    assert page.evaluate("getComputedStyle(document.documentElement).colorScheme") == "light"
    ctx.close()


@pytest.mark.parametrize("width", [1280, 375])
def test_toggle_target_size_44(browser, site_url, width):
    ctx = _ctx(browser, width, scheme="light")
    page = open_page(ctx, site_url, "index")
    box = page.locator(".nav .theme-toggle").bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44, box
    if width < 880:
        page.locator(".nav-toggle").click()
        drawer_btn = page.locator(".mobile-drawer .theme-toggle")
        drawer_btn.wait_for(state="visible")
        box = drawer_btn.bounding_box()
        assert box["width"] >= 44 and box["height"] >= 44, box
    ctx.close()


@pytest.mark.parametrize("width", [1280, 375])
def test_theme_switch_does_not_shift_layout(browser, site_url, width):
    ctx = _ctx(browser, width, scheme="light")
    page = open_page(ctx, site_url, "index")
    probe = """() => {
      const r = s => { const e = document.querySelector(s); if (!e) return null; const b = e.getBoundingClientRect(); return [b.x, b.y + scrollY, b.width, b.height].map(Math.round); };
      return {h: document.documentElement.scrollHeight, w: document.documentElement.scrollWidth,
        rects: ['.nav', '.nav .logo', '.nav .theme-toggle', 'main', 'main h1', 'footer', '.mobile-drawer'].map(r)};
    }"""
    page.wait_for_timeout(800)  # let load-time content (lazy images, counters) settle before measuring
    before = page.evaluate(probe)
    assert page.evaluate(probe) == before
    page.locator(".nav .theme-toggle").click()
    page.wait_for_timeout(350)
    assert page.evaluate(probe) == before
    ctx.close()
