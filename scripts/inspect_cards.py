from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('http://localhost:3000/console')
    page.wait_for_timeout(2000)

    print("=== JUDGE CONTROL PANEL ===")
    cards = page.query_selector_all('div.rounded-2xl, div.rounded-xl')
    for i, c in enumerate(cards):
        txt = c.inner_text().strip().replace('\n', ' | ')
        if "Invariant" in txt or "Batch" in txt or "Ambiguity" in txt or "Test" in txt:
            print(f"Card {i}: {txt[:120]}...")
            
    print("\n=== CLICKING ASSURANCE LIFECYCLE ===")
    btn_life = page.get_by_text("Assurance Lifecycle")
    if btn_life:
        btn_life.click()
        page.wait_for_timeout(1000)
        stages = page.query_selector_all('button, h3, h4')
        for s in stages:
            st = s.inner_text().strip().replace('\n', ' ')
            if any(k in st for k in ["Stage", "HELD", "VERIFYING", "REFUSED", "CORRECTED", "RELEASING", "RELEASED"]):
                print("Stage element:", st[:80])

    print("\n=== CLICKING SECURITY PROOF MATRIX ===")
    btn_sec = page.get_by_text("Security Proof & Attack Matrix")
    if btn_sec:
        btn_sec.click()
        page.wait_for_timeout(1000)
        attacks = page.query_selector_all('h3, h4, span')
        for a in attacks:
            at = a.inner_text().strip()
            if any(k in at for k in ["Missing Auth", "Forged", "IDOR", "HMAC", "Float", "Replay"]):
                print("Attack vector:", at[:60])
                
    browser.close()
