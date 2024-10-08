"""This class handles the captcha solving for playwright users"""

import logging
import random
import time
from typing import Any

from playwright.sync_api import FloatRect, Page, expect
from playwright.sync_api import TimeoutError

from . import selectors
from .captchatype import CaptchaType
from .solver import Solver
from .api import ApiClient
from .downloader import fetch_image_b64
from .geometry import compute_puzzle_slide_distance, compute_rotate_slide_distance

class PlaywrightSolver(Solver):

    client: ApiClient
    page: Page

    def __init__(
            self,
            page: Page,
            sadcaptcha_api_key: str,
            headers: dict[str, Any] | None = None,
            proxy: str | None = None
        ) -> None:
        self.page = page
        self.client = ApiClient(sadcaptcha_api_key)
        self.headers = headers
        self.proxy = proxy

    def captcha_is_present(self, timeout: int = 15) -> bool:
        if self.page_is_douyin():
            try:
                douyin_locator = self.page.frame_locator(selectors.DouyinPuzzle.FRAME).locator("*")
                expect(douyin_locator.first).not_to_have_count(0)
            except (TimeoutError, AssertionError):
                return False
        else:
            try:
                tiktok_locator = self.page.locator(f"{selectors.Wrappers.V1}, {selectors.Wrappers.V2}")
                expect(tiktok_locator.first).to_be_visible(timeout=timeout * 1000)
                logging.debug("v1 or v2 tiktok selector present")
            except (TimeoutError, AssertionError):
                return False
        return True

    def captcha_is_not_present(self, timeout: int = 15) -> bool:
        if self.page_is_douyin():
            try:
                douyin_locator = self.page.frame_locator(selectors.DouyinPuzzle.FRAME).locator("*")
                expect(douyin_locator.first).to_have_count(0)
            except (TimeoutError, AssertionError):
                return False
        else:
            try:
                tiktok_locator = self.page.locator(f"{selectors.Wrappers.V1}, {selectors.Wrappers.V2}")
                expect(tiktok_locator.first).to_have_count(0, timeout=timeout * 1000)
                logging.debug("v1 or v2 tiktok selector not present")
            except (TimeoutError, AssertionError):
                return False
        return True

    def identify_captcha(self) -> CaptchaType:
        for _ in range(60):
            if self._any_selector_in_list_present([selectors.PuzzleV1.UNIQUE_IDENTIFIER]):
                logging.debug("detected puzzle")
                return CaptchaType.PUZZLE_V1
            if self._any_selector_in_list_present([selectors.PuzzleV2.UNIQUE_IDENTIFIER]):
                logging.debug("detected puzzle v2")
                return CaptchaType.PUZZLE_V2
            elif self._any_selector_in_list_present([selectors.RotateV1.UNIQUE_IDENTIFIER]):
                logging.debug("detected rotate v1")
                return CaptchaType.ROTATE_V1
            elif self._any_selector_in_list_present([selectors.RotateV2.UNIQUE_IDENTIFIER]):
                logging.debug("detected rotate v2")
                return CaptchaType.ROTATE_V2
            if self._any_selector_in_list_present([selectors.ShapesV1.UNIQUE_IDENTIFIER]):
                img_url = self._get_image_url(selectors.ShapesV1.IMAGE)
                if "/icon" in img_url:
                    logging.debug("detected icon v1")
                    return CaptchaType.ICON_V1
                elif "/3d" in img_url:
                    logging.debug("detected shapes v1")
                    return CaptchaType.SHAPES_V1
                else:
                    logging.warn("did not see '/3d' in image source url but returning shapes v1 anyways")
                    return CaptchaType.SHAPES_V1
            if self._any_selector_in_list_present([selectors.ShapesV2.UNIQUE_IDENTIFIER]):
                img_url = self._get_image_url(selectors.ShapesV2.IMAGE)
                if "/icon" in img_url:
                    logging.debug("detected icon v2")
                    return CaptchaType.ICON_V2
                elif "/3d" in img_url:
                    logging.debug("detected shapes v2")
                    return CaptchaType.SHAPES_V2
                else:
                    logging.warn("did not see '/3d' in image source url but returning shapes v2 anyways")
                    return CaptchaType.SHAPES_V2
            else:
                time.sleep(0.5)
        raise ValueError("Neither puzzle, shapes, or rotate captcha was present.")

    def page_is_douyin(self) -> bool:
        if "douyin" in self.page.url:
            logging.debug("page is douyin")
            return True
        logging.debug("page is tiktok")
        return False

    def solve_shapes(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.ShapesV1.IMAGE]):
                logging.debug("Went to solve shapes but #captcha-verify-image was not present")
                return
            image = fetch_image_b64(self._get_image_url(selectors.ShapesV1.IMAGE), headers=self.headers, proxy=self.proxy)
            solution = self.client.shapes(image)
            image_element = self.page.locator(selectors.ShapesV1.IMAGE)
            bounding_box = image_element.bounding_box()
            if not bounding_box:
                raise AttributeError("Image element was found but had no bounding box")
            self._click_proportional(bounding_box, solution.point_one_proportion_x, solution.point_one_proportion_y)
            self._click_proportional(bounding_box, solution.point_two_proportion_x, solution.point_two_proportion_y)
            self.page.locator(selectors.ShapesV1.SUBMIT_BUTTON).click()
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_shapes_v2(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.ShapesV2.IMAGE]):
                logging.debug("Went to solve shapes but image was not present")
                return
            image = fetch_image_b64(self._get_image_url(selectors.ShapesV2.IMAGE), headers=self.headers, proxy=self.proxy)
            solution = self.client.shapes(image)
            image_element = self.page.locator(selectors.ShapesV2.IMAGE)
            bounding_box = image_element.bounding_box()
            if not bounding_box:
                raise AttributeError("Image element was found but had no bounding box")
            self._click_proportional(bounding_box, solution.point_one_proportion_x, solution.point_one_proportion_y)
            self._click_proportional(bounding_box, solution.point_two_proportion_x, solution.point_two_proportion_y)
            self.page.locator(selectors.ShapesV2.SUBMIT_BUTTON).click()
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_rotate(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.RotateV1.INNER]):
                logging.debug("Went to solve rotate but whirl-inner-img was not present")
                return
            outer = fetch_image_b64(self._get_image_url(selectors.RotateV1.OUTER), headers=self.headers, proxy=self.proxy)
            inner = fetch_image_b64(self._get_image_url(selectors.RotateV1.INNER), headers=self.headers, proxy=self.proxy)
            solution = self.client.rotate(outer, inner)
            logging.debug(f"Solution angle: {solution}")
            slide_bar_width = self._get_element_width(selectors.RotateV1.SLIDE_BAR)
            slider_button_width = self._get_element_width(selectors.RotateV1.SLIDER_DRAG_BUTTON)
            distance = compute_rotate_slide_distance(solution.angle, slide_bar_width, slider_button_width)
            logging.debug(f"Solution distance: {distance}")
            self._drag_element_horizontal(selectors.RotateV1.SLIDER_DRAG_BUTTON, distance)
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_rotate_v2(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.RotateV2.INNER]):
                logging.debug("Went to solve rotate but whirl-inner-img was not present")
                return
            outer = fetch_image_b64(self._get_image_url(selectors.RotateV2.OUTER), headers=self.headers, proxy=self.proxy)
            inner = fetch_image_b64(self._get_image_url(selectors.RotateV2.INNER), headers=self.headers, proxy=self.proxy)
            solution = self.client.rotate(outer, inner)
            logging.debug(f"Solution angle: {solution}")
            slide_bar_width = self._get_element_width(selectors.RotateV2.SLIDE_BAR)
            slider_button_width = self._get_element_width(selectors.RotateV2.SLIDER_DRAG_BUTTON)
            distance = compute_rotate_slide_distance(solution.angle, slide_bar_width, slider_button_width)
            logging.debug(f"Solution distance: {distance}")
            self._drag_element_horizontal(selectors.RotateV2.SLIDER_DRAG_BUTTON, distance)
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_puzzle(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.PuzzleV1.PIECE]):
                logging.debug("Went to solve puzzle but piece image was not present")
                return
            puzzle = fetch_image_b64(self._get_image_url(selectors.PuzzleV1.PUZZLE), headers=self.headers, proxy=self.proxy)
            piece = fetch_image_b64(self._get_image_url(selectors.PuzzleV1.PIECE), headers=self.headers, proxy=self.proxy)
            solution = self.client.puzzle(puzzle, piece)
            puzzle_width = self._get_element_width(selectors.PuzzleV1.PUZZLE)
            distance = compute_puzzle_slide_distance(solution.slide_x_proportion, puzzle_width)
            self._drag_element_horizontal(selectors.PuzzleV1.SLIDER_DRAG_BUTTON, distance)
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_puzzle_v2(self, retries: int = 3) -> None:
        for _ in range(retries):
            if not self._any_selector_in_list_present([selectors.PuzzleV2.PIECE]):
                logging.debug("Went to solve puzzle but piece image was not present")
                return
            puzzle = fetch_image_b64(self._get_image_url(selectors.PuzzleV2.PUZZLE), headers=self.headers, proxy=self.proxy)
            piece = fetch_image_b64(self._get_image_url(selectors.PuzzleV2.PIECE), headers=self.headers, proxy=self.proxy)
            solution = self.client.puzzle(puzzle, piece)
            puzzle_width = self._get_element_width(selectors.PuzzleV2.PUZZLE)
            distance = compute_puzzle_slide_distance(solution.slide_x_proportion, puzzle_width)
            self._drag_element_horizontal(selectors.PuzzleV2.SLIDER_DRAG_BUTTON, distance)
            if self.captcha_is_not_present(timeout=5):
                return
            else:
                time.sleep(5)

    def solve_icon(self) -> None:
        if not self._any_selector_in_list_present([selectors.IconV1.IMAGE]):
            logging.debug("Went to solve icon captcha but #captcha-verify-image was not present")
            return
        challenge = self._get_element_text(selectors.IconV1.TEXT)
        image = fetch_image_b64(self._get_image_url(selectors.IconV1.IMAGE), headers=self.headers, proxy=self.proxy)
        solution = self.client.icon(challenge, image)
        image_element = self.page.locator(selectors.IconV1.IMAGE)
        bounding_box = image_element.bounding_box()
        if not bounding_box:
            raise AttributeError("Image element was found but had no bounding box")
        for point in solution.proportional_points:
            self._click_proportional(bounding_box, point.proportion_x, point.proportion_y)
        self.page.locator(selectors.IconV1.SUBMIT_BUTTON).click()

    def solve_icon_v2(self) -> None:
        if not self._any_selector_in_list_present([selectors.IconV2.IMAGE]):
            logging.debug("Went to solve icon captcha but #captcha-verify-image was not present")
            return
        challenge = self._get_element_text(selectors.IconV2.TEXT)
        image = fetch_image_b64(selectors.IconV2.IMAGE, headers=self.headers, proxy=self.proxy)
        solution = self.client.icon(challenge, image)
        image_element = self.page.locator(selectors.IconV2.IMAGE)
        bounding_box = image_element.bounding_box()
        if not bounding_box:
            raise AttributeError("Image element was found but had no bounding box")
        for point in solution.proportional_points:
            self._click_proportional(bounding_box, point.proportion_x, point.proportion_y)
        self.page.locator(selectors.IconV2.SUBMIT_BUTTON).click()

    def solve_douyin_puzzle(self) -> None:
        puzzle = fetch_image_b64(self._get_douyin_puzzle_image_url(), headers=self.headers, proxy=self.proxy)
        piece = fetch_image_b64(self._get_douyin_piece_image_url(), headers=self.headers, proxy=self.proxy)
        solution = self.client.puzzle(puzzle, piece)
        distance = self._compute_douyin_puzzle_slide_distance(solution.slide_x_proportion)
        self._drag_element_horizontal(".captcha-slider-btn", distance, frame_selector=selectors.DouyinPuzzle.FRAME)

    def _get_douyin_puzzle_image_url(self) -> str:
        e = self.page.frame_locator(selectors.DouyinPuzzle.FRAME).locator(selectors.DouyinPuzzle.PUZZLE)
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Puzzle image URL was None")
        return url

    def _compute_douyin_puzzle_slide_distance(self, proportion_x: float) -> int:
        e = self.page.frame_locator(selectors.DouyinPuzzle.FRAME).locator(selectors.DouyinPuzzle.PUZZLE)
        box = e.bounding_box()
        if box:
            return int(proportion_x * box["width"])
        raise AttributeError("#captcha-verify-image was found but had no bouding box")

    def _get_douyin_piece_image_url(self) -> str:
        e = self.page.frame_locator(selectors.DouyinPuzzle.FRAME).locator(selectors.DouyinPuzzle.PIECE)
        url = e.get_attribute("src")
        if not url:
            raise ValueError("Piece image URL was None")
        return url

    def _get_element_text(self, selector: str) -> str:
        challenge_element = self.page.locator(selector)
        text = challenge_element.text_content()
        if not text:
            raise ValueError("element was found but did not have any text.")
        return text

    def _get_element_width(self, selector: str) -> int:
        e = self.page.locator(selector)
        box = e.bounding_box()
        if box:
            return int(box["width"])
        raise AttributeError("element was found but had no bouding box")

    def _get_image_url(self, selector: str) -> str:
        e = self.page.locator(selector)
        url = e.get_attribute("src")
        if not url:
            raise ValueError("image URL was None")
        return url

    def _click_proportional(
            self,
            bounding_box: FloatRect,
            proportion_x: float,
            proportion_y: float
        ) -> None:
        """Click an element inside its bounding box at a point defined by the proportions of x and y
        to the width and height of the entire element

        Args:
            element: FloatRect to click inside
            proportion_x: float from 0 to 1 defining the proportion x location to click 
            proportion_y: float from 0 to 1 defining the proportion y location to click 
        """
        x_origin = bounding_box["x"]
        y_origin = bounding_box["y"]
        x_offset = (proportion_x * bounding_box["width"])
        y_offset = (proportion_y * bounding_box["height"]) 
        self.page.mouse.move(x_origin + x_offset, y_origin + y_offset)
        time.sleep(random.randint(1, 10) / 11)
        self.page.mouse.down()
        time.sleep(0.001337)
        self.page.mouse.up()
        time.sleep(random.randint(1, 10) / 11)

    def _drag_element_horizontal(self, css_selector: str, x_offset: int, frame_selector: str | None = None) -> None:
        if frame_selector:
            e = self.page.frame_locator(frame_selector).locator(css_selector)
        else:
            e = self.page.locator(css_selector)
        box = e.bounding_box()
        if not box:
            raise AttributeError("Element had no bounding box")
        start_x = (box["x"] + (box["width"] / 1.337))
        start_y = (box["y"] +  (box["height"] / 1.337))
        self.page.mouse.move(start_x, start_y)
        time.sleep(random.randint(1, 10) / 11)
        self.page.mouse.down()
        for pixel in range(0, x_offset + 5):
            self.page.mouse.move(start_x + pixel, start_y)
            time.sleep(0.01)
        time.sleep(0.25)
        for pixel in range(-5, 2):
            self.page.mouse.move(start_x + x_offset - pixel, start_y + pixel) # overshoot back
            time.sleep(0.05)
        time.sleep(0.2)
        self.page.mouse.move(start_x + x_offset, start_y, steps=75) 
        time.sleep(0.3)
        self.page.mouse.up()

    def _any_selector_in_list_present(self, selectors: list[str]) -> bool:
        for selector in selectors:
            for ele in self.page.locator(selector).all():
                if ele.is_visible():
                    logging.debug("Detected selector: " + selector + " from list " + ", ".join(selectors))
                    return True
        logging.debug("No selector in list found: " + ", ".join(selectors))
        return False
