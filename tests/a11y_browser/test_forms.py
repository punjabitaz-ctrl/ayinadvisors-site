"""Form error flow: errors are announced, name the fields, and focus moves to the first problem."""
import pytest

from a11y_browser.conftest import new_context, open_page

pytestmark = pytest.mark.browser

FORMS = [
    ("Contact", "#consult-form", "#form-error", ["name", "company", "email"], "Full name"),
    ("BizCheck", "#bizcheck-form", "#bc-error", ["bc_name", "bc_company", "bc_email", "bc_desc"], "Full name"),
]


@pytest.mark.parametrize("stem,form,err,required,first_label", FORMS, ids=[f[0] for f in FORMS])
def test_empty_submit_flags_every_required_field(browser, site_url, stem, form, err, required, first_label):
    ctx = new_context(browser, 1280, 900)
    try:
        page = open_page(ctx, site_url, stem)
        page.locator(f"{form} button[type=submit]").click()
        alert = page.locator(err)
        assert alert.get_attribute("role") == "alert"
        text = alert.inner_text()
        assert first_label in text, f"error text does not name the fields: {text!r}"
        for fid in required:
            el = page.locator(f"#{fid}")
            assert el.get_attribute("aria-invalid") == "true", f"{fid} not marked aria-invalid"
            assert el.get_attribute("aria-describedby") == err[1:], f"{fid} not tied to the error message"
        assert page.evaluate("document.activeElement.id") == required[0], "focus did not move to the first invalid field"
    finally:
        ctx.close()


@pytest.mark.parametrize("stem,form,err,required,first_label", FORMS, ids=[f[0] for f in FORMS])
def test_bad_email_is_flagged_and_fixed_fields_are_cleared(browser, site_url, stem, form, err, required, first_label):
    ctx = new_context(browser, 1280, 900)
    try:
        page = open_page(ctx, site_url, stem)
        for fid in required:
            page.locator(f"#{fid}").fill("not-an-email" if fid.endswith("email") else "x")
        page.locator(f"{form} button[type=submit]").click()
        email = required[2]
        assert page.locator(f"#{email}").get_attribute("aria-invalid") == "true"
        assert page.locator(f"#{required[0]}").get_attribute("aria-invalid") is None
        assert page.evaluate("document.activeElement.id") == email
        page.locator(f"#{email}").fill("someone@example.com")
        page.locator(f"{form} button[type=submit]").click()
        assert page.locator(f"#{email}").get_attribute("aria-invalid") is None, "stale aria-invalid after the field was fixed"
    finally:
        ctx.close()
