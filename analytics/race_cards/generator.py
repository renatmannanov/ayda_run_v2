"""
Race card image generator using Playwright + Jinja2.
Renders HTML templates to PNG images.
"""
import logging
from typing import List, Optional
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright, Browser, Playwright

from .models import RaceCardData, RaceCardOutput, MedalType

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent / "templates"

# Card dimensions (preview size - will be scaled for export)
PREVIEW_WIDTH = 405
PREVIEW_HEIGHT = 506
EXPORT_SCALE = 2.667  # 1080 / 405 = 2.667 for final 1080px width


class RaceCardGenerator:
    """
    Generates race result cards as PNG images.
    Uses Jinja2 for templating and Playwright for rendering.
    """

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=True
        )
        # Register custom filters
        self._jinja_env.filters['medal_class'] = self._medal_class
        self._jinja_env.filters['medal_icon'] = self._medal_icon

    @staticmethod
    def _medal_class(medal: MedalType) -> str:
        """Get CSS class for medal styling."""
        return {
            MedalType.GOLD: "gold",
            MedalType.SILVER: "silver",
            MedalType.BRONZE: "bronze",
            MedalType.NONE: "",
        }.get(medal, "")

    @staticmethod
    def _medal_icon(medal: MedalType) -> str:
        """Get emoji icon for medal."""
        return {
            MedalType.GOLD: "🥇",
            MedalType.SILVER: "🥈",
            MedalType.BRONZE: "🥉",
            MedalType.NONE: "",
        }.get(medal, "")

    async def _get_browser(self) -> Browser:
        """Get or create browser instance."""
        if self._browser is None or not self._browser.is_connected():
            if self._playwright is None:
                self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser

    async def close(self):
        """Close browser and playwright instances."""
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    def _render_template(self, template_name: str, data: RaceCardData) -> str:
        """Render Jinja2 template with data."""
        template = self._jinja_env.get_template(template_name)
        return template.render(
            participant=data.participant,
            event=data.event,
            medal=data.participant.medal,
            has_elevation=data.participant.has_elevation_data,
        )

    async def _html_to_png(
        self,
        html: str,
        width: int = PREVIEW_WIDTH,
        height: int = PREVIEW_HEIGHT,
        scale: float = EXPORT_SCALE
    ) -> bytes:
        """
        Render HTML to PNG using Playwright.

        Args:
            html: Complete HTML string
            width: Viewport width (preview size)
            height: Viewport height (preview size)
            scale: Scale factor for export (default 2.667 for 1080px)

        Returns:
            PNG image as bytes
        """
        browser = await self._get_browser()
        page = await browser.new_page(
            viewport={"width": width, "height": height},
            device_scale_factor=scale
        )

        try:
            # Set content and wait for fonts to load
            await page.set_content(html, wait_until="networkidle")

            # Wait for Google Fonts to load
            await page.wait_for_timeout(1000)

            # Take screenshot of the card element
            screenshot = await page.screenshot(
                type="png",
                full_page=False,
                clip={"x": 0, "y": 0, "width": width, "height": height}
            )

            return screenshot

        finally:
            await page.close()

    async def generate_single_post(self, data: RaceCardData) -> bytes:
        """
        Generate Format A: Single post card (1080x1350).

        Args:
            data: Race card data

        Returns:
            PNG image bytes
        """
        logger.info(f"Generating single post for {data.participant.name}")
        html = self._render_template("single_post.html", data)
        return await self._html_to_png(html, width=PREVIEW_WIDTH, height=PREVIEW_HEIGHT)

    async def generate_carousel(self, data: RaceCardData) -> List[bytes]:
        """
        Generate Format B: 3-slide carousel.

        Args:
            data: Race card data

        Returns:
            List of 3 PNG images (bytes)
        """
        logger.info(f"Generating carousel for {data.participant.name}")
        slides = []

        # Slide 1: Main result
        html1 = self._render_template("carousel_slide_1.html", data)
        slides.append(await self._html_to_png(html1))

        # Slide 2: Details (template handles variant selection based on has_elevation)
        html2 = self._render_template("carousel_slide_2.html", data)
        slides.append(await self._html_to_png(html2))

        # Slide 3: Splits + credits
        html3 = self._render_template("carousel_slide_3.html", data)
        slides.append(await self._html_to_png(html3))

        return slides

    async def generate_all(self, data: RaceCardData) -> RaceCardOutput:
        """
        Generate all card formats.

        Args:
            data: Race card data

        Returns:
            RaceCardOutput with all images
        """
        logger.info(f"Generating all cards for {data.participant.name}")

        single_post = await self.generate_single_post(data)
        carousel = await self.generate_carousel(data)

        logger.info(f"Generated {1 + len(carousel)} cards total")

        return RaceCardOutput(
            single_post=single_post,
            carousel_slides=carousel
        )


# Singleton
_generator_instance: Optional[RaceCardGenerator] = None


async def get_generator() -> RaceCardGenerator:
    """Get singleton generator instance."""
    global _generator_instance
    if _generator_instance is None:
        _generator_instance = RaceCardGenerator()
    return _generator_instance
