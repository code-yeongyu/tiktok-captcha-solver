"""Abstract base class for Tiktok Captcha Async Solvers"""

import asyncio
from abc import ABC, abstractmethod

from undetected_chromedriver import logging

from .captchatype import CaptchaType

class AsyncSolver(ABC):

    async def solve_captcha_if_present(self, captcha_detect_timeout: int = 15, retries: int = 3) -> None:
        """Solves any captcha that is present, if one is detected

        Args:
            captcha_detect_timeout: return if no captcha is detected in this many seconds
            retries: number of times to retry captcha
        """
        for _ in range(retries):
            if not await self.captcha_is_present(captcha_detect_timeout):
                logging.debug("Captcha is not present")
                return
            if self.page_is_douyin():
                logging.debug("Solving douyin puzzle")
                try:
                    await self.solve_douyin_puzzle()
                except ValueError as e:
                    logging.debug("Douyin puzzle was not ready, trying again in 5 seconds")
            else:
                match await self.identify_captcha():
                    case CaptchaType.PUZZLE_V1: 
                        logging.debug("Detected puzzle v1")
                        await self.solve_puzzle()
                    case CaptchaType.PUZZLE_V2: 
                        logging.debug("Detected puzzle v2")
                        await self.solve_puzzle_v2()
                    case CaptchaType.ROTATE_V1: 
                        logging.debug("Detected rotate v1")
                        await self.solve_rotate()
                    case CaptchaType.ROTATE_V2: 
                        logging.debug("Detected rotate v2")
                        await self.solve_rotate_v2()
                    case CaptchaType.SHAPES_V1: 
                        logging.debug("Detected shapes v2")
                        await self.solve_shapes()
                    case CaptchaType.SHAPES_V2: 
                        logging.debug("Detected shapes v2")
                        await self.solve_shapes_v2()
                    case CaptchaType.ICON_V1:
                        logging.debug("Detected icon v1")
                        await self.solve_icon()
                    case CaptchaType.ICON_V2:
                        logging.debug("Detected icon v2")
                        await self.solve_icon_v2()
            if await self.captcha_is_not_present(timeout=5):
                return
            else:
                await asyncio.sleep(5)

    @abstractmethod
    async def captcha_is_present(self, timeout: int = 15) -> bool:
        pass

    @abstractmethod
    async def captcha_is_not_present(self, timeout: int = 15) -> bool:
        pass

    @abstractmethod
    async def identify_captcha(self) -> CaptchaType:
        pass

    @abstractmethod
    def page_is_douyin(self) -> bool:
        pass

    @abstractmethod
    async def solve_shapes(self) -> None:
        pass

    @abstractmethod
    async def solve_shapes_v2(self) -> None:
        pass

    @abstractmethod
    async def solve_rotate(self) -> None:
        pass

    @abstractmethod
    async def solve_rotate_v2(self) -> None:
        pass

    @abstractmethod
    async def solve_puzzle(self) -> None:
        pass

    @abstractmethod
    async def solve_puzzle_v2(self) -> None:
        pass

    @abstractmethod
    async def solve_icon(self) -> None:
        pass

    @abstractmethod
    async def solve_icon_v2(self) -> None:
        pass

    @abstractmethod
    async def solve_douyin_puzzle(self) -> None:
        pass



