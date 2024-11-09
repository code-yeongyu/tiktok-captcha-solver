# TikTok Captcha Solver API
This project is the [SadCaptcha TikTok Captcha Solver](https://www.sadcaptcha.com?ref=ghclientrepo) API client.
The purpose is to make integrating SadCaptcha into your Selenium, Playwright, or Async Playwright app as simple as one line of code.
Instructions for integrating with Selenium, Playwright, and Async Playwright are described below in their respective sections. 
This API also works on mobile devices (Appium, etc.). 

This tool works on both TikTok and Douyin and can solve any of the four captcha challenges pictured below:

<div align="center">
    <img src="https://sadcaptcha.b-cdn.net/tiktok3d.webp" width="100" alt="TikTok Captcha Solver">
    <img src="https://sadcaptcha.b-cdn.net/tiktokrotate.webp" width="100" alt="TikTok Captcha Solver">
    <img src="https://sadcaptcha.b-cdn.net/tiktokpuzzle.webp" width="100" alt="TikTok Captcha Solver">
    <img src="https://sadcaptcha.b-cdn.net/tiktokicon.webp" width="100" alt="TikTok Captcha Solver">
    <br/>
</div>

## Requirements
- Python >= 3.10
- **If using Selenium** - Selenium properly installed and in `PATH`
- **If using Playwright** - Playwright must be properly installed with `playwright install`
- **If using mobile** - Appium and opencv must be properly installed
- **Stealth plugin** - You must use the appropriate `stealth` plugin for whichever browser automation framework you are using.
    - For Selenium, you can use [undetected-chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)
    - For Playwright, you can use [playwright-stealth](https://pypi.org/project/playwright-stealth/)

## Installation
This project can be installed with `pip`. Just run the following command:
```
pip install tiktok-captcha-solver
```

## Selenium Client 
Import the package, set up the `SeleniumSolver` class, and call it whenever you need.
This turns the entire captcha detection, solution, retry, and verification process into a single line of code.
It is the recommended method if you are using selenium.

```py
from tiktok_captcha_solver import SeleniumSolver
from selenium_stealth import stealth
import undetected_chromedriver as uc

driver = uc.Chrome(headless=False) # Use default undetected_chromedriver configuration!
api_key = "YOUR_API_KEY_HERE"
sadcaptcha = SeleniumSolver(driver, api_key)

# Selenium code that causes a TikTok or Douyin captcha...

sadcaptcha.solve_captcha_if_present()
```

It is crucial that you use `undetected_chromedriver` with the default configuration, instead of the standard Selenium chromedriver.
Failure to use the `undetected_chromedriver` will result in "Verification failed" when attempting to solve the captcha.

## Playwright Client
Import the package, set up the `PlaywrightSolver` class, and call it whenever you need.
This turns the entire captcha detection, solution, retry, and verification process into a single line of code.
It is the recommended method if you are using playwright.


```py
from tiktok_captcha_solver import PlaywrightSolver
from playwright.sync_api import Page, sync_playwright
from playwright_stealth import stealth_sync, StealthConfig

api_key = "YOUR_API_KEY_HERE"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
    stealth_sync(page, config) # Use correct playwright_stealth configuration!
    
    # Playwright code that causes a TikTok or Douyin captcha...

    sadcaptcha = PlaywrightSolver(page, api_key)
    sadcaptcha.solve_captcha_if_present()
```
It is crucial that users of the Playwright client also use `playwright-stealth` with the configuration specified above.
Failure to use the `playwright-stealth` plugin will result in "Verification failed" when attempting to solve the captcha.

## Async Playwright Client
Import the package, set up the `AsyncPlaywrightSolver` class, and call it whenever you need.
This turns the entire captcha detection, solution, retry, and verification process into a single line of code.
It is the recommended method if you are using async playwright.



```py
import asyncio
from tiktok_captcha_solver import AsyncPlaywrightSolver
from playwright.async_api import Page, async_playwright
from playwright_stealth import stealth_async, StealthConfig

api_key = "YOUR_API_KEY_HERE"

async def main()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        config = StealthConfig(navigator_languages=False, navigator_vendor=False, navigator_user_agent=False)
        await stealth_async(page, config) # Use correct playwright_stealth configuration!
        
        # Playwright code that causes a TikTok or Douyin captcha...

        sadcaptcha = AsyncPlaywrightSolver(page, api_key)
        await sadcaptcha.solve_captcha_if_present()

asyncio.run(main())
```
It is crucial that users of the Playwright client also use `playwright-stealth` with the stealth configuration specified above.
Failure to use the `playwright-stealth` plugin will result in "Verification failed" when attempting to solve the captcha.

## Mobile (Appium)
Currently there is no premade solver for Mobile/appium, but you can implement the API with relative ease.
The idea is that you take a screenshot using the mobile driver, crop the images, and then send the images to the API.
Once you've done that, you can consume the response.
Here is a working example for Puzzle and Rotate captcha. 
keep in mind, you will need to adjust the `captcha_box` and `offset_x` varaibles according to your particular mobile device.

```py
from PIL import Image, ImageDraw
import base64
import requests

# SOLVING PUZZLE CAPTCHA
BASE_URL = 'https://www.sadcaptcha.com/api/v1'
LICENSE_KEY = ''
puzzle_url = f'{BASE_URL}/puzzle?licenseKey={LICENSE_KEY}'

def solve_puzzle():
    driver.save_screenshot('puzzle.png')

    full_image = Image.open('puzzle.png')
    captcha_box1 = (165, 1175, 303, 1330)
    captcha_image1 = full_image.crop(captcha_box1)
    captcha_image1.save('puzzle_screenshot.png')

    captcha_box2 = (300, 945, 1016, 1475)
    captcha_image2 = full_image.crop(captcha_box2)
    captcha_image2.save('puzzle_screenshot1.png')

    draw = ImageDraw.Draw(captcha_image1)
    draw.ellipse([(0, 0), (captcha_image1.width / 4, captcha_image1.height)], fill="blue", outline="blue")

    with open('puzzle_screenshot.png', 'rb') as f:
        puzzle = base64.b64encode(f.read()).decode()
    with open('puzzle_screenshot1.png', 'rb') as f:
        piece = base64.b64encode(f.read()).decode()

    data = {
        'puzzleImageB64': puzzle,
        'pieceImageB64': piece
    }

    r = requests.post(puzzle_url, json=data)

    slide_x_proportion = r.json().get('slideXProportion')

    offset_x = 46 + (46 * float(slide_x_proportion))

    driver.swipe(start_x=55, start_y=530, end_x=55 + int(offset_x), end_y=530, duration=1000)
    time.sleep(3)


# SOLVING ROTATE CAPTCHA
BASE_URL = 'https://www.sadcaptcha.com/api/v1'
LICENSE_KEY = ''
rotate_url = f'{BASE_URL}/rotate?licenseKey={LICENSE_KEY}'

def solve_rotate():
    driver.save_screenshot('full_screenshot.png')

    full_image = Image.open('full_screenshot.png')

    captcha_box1 = (415, 1055, 755, 1395)
    captcha_image1 = full_image.crop(captcha_box1)

    mask = Image.new('L', captcha_image1.size, 0)
    draw = ImageDraw.Draw(mask)
    circle_bbox = (0, 0, captcha_image1.size[0], captcha_image1.size[1])
    draw.ellipse(circle_bbox, fill=255)

    captcha_image1.putalpha(mask)
    captcha_image1.save('captcha_image_circular.png')

    captcha_box2 = (318, 958, 852, 1492)
    captcha_image2 = full_image.crop(captcha_box2)

    mask2 = Image.new('L', captcha_image2.size, 0)
    draw = ImageDraw.Draw(mask2)
    draw.ellipse((captcha_box1[0] - captcha_box2[0], captcha_box1[1] - captcha_box2[1],
                  captcha_box1[2] - captcha_box2[0], captcha_box1[3] - captcha_box2[1]), fill=255)

    captcha_image_with_hole = captcha_image2.copy()
    captcha_image_with_hole.paste((0, 0, 0, 0), (0, 0), mask2)
    captcha_image_with_hole.save('captcha_image_with_hole.png')

    with open('captcha_image_with_hole.png', 'rb') as f:
        outer = base64.b64encode(f.read()).decode('utf-8')
    with open('captcha_image_circular.png', 'rb') as f:
        inner = base64.b64encode(f.read()).decode('utf-8')

    data = {
        'outerImageB64': outer,
        'innerImageB64': inner
    }

    r = requests.post(rotate_url, json=data)
    r.raise_for_status()
    response = r.json()
    angle = response.get('angle', 0)

    result = ((286 - 55) * angle) / 360
    start_x = 55
    start_y = 530
    offset_x = result

    driver.swipe(start_x, start_y, start_x + int(offset_x), start_y, duration=1000)
```

## Using Proxies and Custom Headers
SadCaptcha supports using proxies and custom headers such as user agent.
This is useful to avoid detection.
To implement this feature, pass your proxy URL and headers dictionary as a keyword argument to the constructor of the solver.
```py
api_key = "YOUR_API_KEY_HERE"
proxy = "http://username:password@123.0.1.2:80"
headers = {"User-Agent": "Chrome"}

# With Selenium Solver
driver = uc.Chrome(headless=False) # Use default undetected_chromedriver configuration!
api_key = "YOUR_API_KEY_HERE"
sadcaptcha = SeleniumSolver(driver, api_key, proxy=proxy, headers=headers)

# With Playwright Solver
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    stealth_sync(page) # Use default playwright_stealth configuration!
    sadcaptcha = PlaywrightSolver(page, api_key, proxy=proxy, headers=headers)
    sadcaptcha.solve_captcha_if_present()

# With Async PlaywrightSolver
async def main()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await stealth_async(page) # Use default playwright_stealth configuration!
        sadcaptcha = AsyncPlaywrightSolver(page, api_key, headers=headers, proxy=proxy)
        await sadcaptcha.solve_captcha_if_present()
```

## API Client
If you are not using Selenium or Playwright, you can still import and use the API client to help you make calls to SadCaptcha
```py
from tiktok_captcha_solver import ApiClient

api_key = "YOUR_API_KEY_HERE"
client = ApiClient(api_key)

# Rotate
res = client.rotate("base64 encoded outer", "base64 encoded inner")

# Puzzle
res = client.puzzle("base64 encoded puzzle", "base64 encoded piece")

# Shapes
res = client.shapes("base64 encoded shapes image")

# Icon (Video upload)
res = client.icon("Which of these objects... ?", base64 encoded icon image")
```

## Troubleshooting
### Captcha solved but still says Verification failed?
This common problem is due to your browser settings. 
If using Selenium, you must use `undetected_chromedriver` with the **default** settings.
If you are using Playwright, you must use the `playwright_stealth` package with the **default** settings.
Do not change the user agent, or modify any other browser characteristics as this is easily detected and flagged as suspicious behavior.

## Contact
- Homepage: https://www.sadcaptcha.com/
- Email: greg@sadcaptcha.com
- Telegram @toughdata
