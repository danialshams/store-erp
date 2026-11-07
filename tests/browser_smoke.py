"""Browser UI test using a controlled local HTTP bridge because browser network
is disabled in this evaluation environment. API requests still hit the real
running FastAPI server, using one persistent cookie jar per browser page.
"""
from pathlib import Path
import httpx
from playwright.sync_api import sync_playwright
base=Path(__file__).parent.parent
css=(base/'public/styles.css').read_text()
js=(base/'public/app.js').read_text()

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
    page=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
    errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    client=httpx.Client(base_url='http://127.0.0.1:8765')
    def fetch_api(url,options):
        res=client.request(options.get('method','GET'),url,content=options.get('body'),headers=options.get('headers') or {})
        return {'status':res.status_code,'body':res.text}
    page.expose_function('erpFetch',fetch_api)
    page.set_content('<html lang="fa" dir="rtl"><meta charset="utf-8"><title>ERP فروشگاهی</title><div id="root"></div><div id="modal-root"></div><div id="toast-root"></div></html>')
    page.add_style_tag(content=css)
    page.evaluate('''() => {window.fetch = async (url,opts={})=>{const x=await window.erpFetch(url,opts);return new Response(x.body,{status:x.status,headers:{'Content-Type':'application/json'}})}}''')
    page.add_script_tag(content=js)
    page.wait_for_selector('[data-auth-tab="register"]')
    page.screenshot(path=str(base/'tests/login-desktop.png'),full_page=True)
    page.locator('[data-auth-tab="register"]').click()
    page.locator('input[name="name"]').fill('کاربر آزمایشی')
    page.locator('input[name="company"]').fill('فروشگاه آزمایشی')
    page.locator('input[name="email"]').fill('test-erp-browser2@example.com')
    page.locator('input[name="password"]').fill('strong-password-123456')
    page.locator('#auth-form button[type="submit"]').click()
    page.wait_for_selector('#top-title',timeout=15000)
    page.wait_for_timeout(300)
    print('Dashboard title:',page.locator('#top-title').inner_text())
    page.screenshot(path=str(base/'tests/dashboard-desktop.png'),full_page=True)
    page.locator('[data-nav="products"]').first.click()
    page.wait_for_selector('#new-record')
    page.locator('#new-record').click()
    page.wait_for_selector('#modal-form')
    page.screenshot(path=str(base/'tests/create-product-desktop.png'),full_page=True)
    print('Form fields:',page.locator('#modal-form input').count())
    print('Browser errors:',errors)
    # Responsive view using same session. Content is still the real web app.
    page.set_viewport_size({'width':390,'height':844})
    page.screenshot(path=str(base/'tests/create-product-mobile.png'),full_page=True)
    page.locator('#modal-close').click()
    page.locator('#menu-toggle').click()
    page.screenshot(path=str(base/'tests/mobile-menu.png'),full_page=True)
    print('Mobile menu class:',page.locator('#shell').get_attribute('class'))
    browser.close()