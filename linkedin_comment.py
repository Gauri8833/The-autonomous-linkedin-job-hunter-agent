"""Navigate to LinkedIn post and post a comment."""
import random
import browser
import config
import terminal_ui


def post_comment(page, post_url, comment_text):
    try:
        page.goto(post_url, wait_until="domcontentloaded", timeout=30000)
        browser.human_delay(2.0, 3.5)
        browser.scroll_page(page, times=1)

        comment_btn_sel = [
            'button[aria-label*="omment"]',
            'button.comment-button',
            'button[data-control-name="comment"]',
            'button:has-text("Comment")',
        ]
        clicked = False
        for sel in comment_btn_sel:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                clicked = True
                break
        if not clicked:
            terminal_ui.print_error("Cannot find comment button.")
            return False

        browser.human_delay(0.8, 1.5)

        editor_sel = [
            '.ql-editor[contenteditable="true"]',
            'div[contenteditable="true"][role="textbox"]',
            '.comments-comment-box__input',
            'div[data-placeholder*="omment"]',
        ]
        editor = None
        for sel in editor_sel:
            editor = page.query_selector(sel)
            if editor:
                break
        if not editor:
            terminal_ui.print_error("Cannot find comment text box.")
            return False

        editor.click()
        browser.human_delay(0.4, 0.9)

        for char in comment_text:
            page.keyboard.type(char)
            delay_ms = random.randint(config.TYPING_SPEED_MIN_MS, config.TYPING_SPEED_MAX_MS)
            browser.human_delay(delay_ms / 1000.0, delay_ms / 1000.0)

        submit_sel = [
            'button.comments-comment-box__submit-button--cr',
            'button.comments-comment-box__submit-button',
            'button[class*="submit"]',
            'button:has-text("Post")',
        ]
        submitted = False
        for sel in submit_sel:
            btn = page.query_selector(sel)
            if btn:
                btn.click()
                submitted = True
                break
        if not submitted:
            terminal_ui.print_error("Cannot find Post button.")
            return False

        browser.human_delay(2.0, 3.5)
        browser.human_delay(1.5, 2.5)
        return True

    except Exception as e:
        terminal_ui.print_error(f"Error posting comment: {e}")
        return False