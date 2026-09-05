from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})
    page.goto('http://localhost:3000/console')
    page.wait_for_timeout(2000)
    buttons = page.query_selector_all('button')
    print(f'Total buttons on /console: {len(buttons)}')
    for i, b in enumerate(buttons):
        text = b.inner_text().strip().replace('\n', ' ')
        if text:
            print(f'Button {i}: "{text[:60]}"')
    browser.close()
