"""
MyRace URL parser using Playwright.
Extracts race result data from live.myrace.info pages.
"""
import re
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse, parse_qs

from playwright.async_api import async_playwright, Browser, Page, Playwright

from .models import ParticipantResult, EventInfo, RaceCardData, Checkpoint

logger = logging.getLogger(__name__)


class MyRaceParseError(Exception):
    """Custom exception for parsing errors."""
    pass


class MyRaceParser:
    """
    Parser for MyRace result pages.
    Uses Playwright to handle JavaScript-rendered content.
    """

    TIMEOUT_MS = 30000  # 30 seconds
    VALID_DOMAINS = ["live.myrace.info", "myrace.info"]

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, str]:
        """
        Validate MyRace URL format.

        Expected format:
        https://live.myrace.info/?f=bases/kz/2026/amangeldyrace2026/amrace2026.clax&B=320

        Returns:
            Tuple of (is_valid, error_message or parsed_bib)
        """
        if not url or not url.strip():
            return False, "URL не может быть пустым"

        try:
            parsed = urlparse(url.strip())

            # Check domain
            if parsed.netloc not in MyRaceParser.VALID_DOMAINS:
                return False, "URL должен быть с сайта live.myrace.info"

            # Check for required parameters
            params = parse_qs(parsed.query)

            if 'f' not in params:
                return False, "В URL отсутствует параметр файла (f=)"

            if 'B' not in params:
                return False, "В URL отсутствует номер участника (B=)"

            bib = params['B'][0]
            return True, bib

        except Exception as e:
            return False, f"Неверный формат URL: {str(e)}"

    @staticmethod
    def extract_url_parts(url: str) -> dict:
        """Extract base path and bib number from URL."""
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        return {
            "base_path": params.get('f', [''])[0],
            "bib": params.get('B', [''])[0],
            "full_url": url
        }

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

    async def parse_result(self, url: str) -> RaceCardData:
        """
        Parse participant result from MyRace URL.

        Args:
            url: Full MyRace URL with bib parameter

        Returns:
            RaceCardData with participant and event info

        Raises:
            MyRaceParseError: If parsing fails
        """
        # Validate URL first
        is_valid, result = self.validate_url(url)
        if not is_valid:
            raise MyRaceParseError(result)

        url_parts = self.extract_url_parts(url)
        browser = await self._get_browser()
        page = await browser.new_page()

        try:
            logger.info(f"Loading MyRace page: {url}")

            # Navigate to page
            await page.goto(url, wait_until="networkidle", timeout=self.TIMEOUT_MS)

            # Wait for results to load - the page uses dynamic JS rendering
            # Try multiple selectors that might indicate data is loaded
            try:
                await page.wait_for_selector(
                    '#results, .results, [class*="result"], table, .content',
                    timeout=self.TIMEOUT_MS
                )
            except Exception:
                logger.warning("Could not find results selector, continuing anyway")

            # Give page time to fully render JS content
            await page.wait_for_timeout(2000)

            # Extract data using JavaScript evaluation
            # MyRace uses a complex JS structure, we need to extract from rendered content
            data = await page.evaluate(r"""
                () => {
                    // Helper to safely get text content
                    const getText = (selector) => {
                        const el = document.querySelector(selector);
                        return el ? el.textContent.trim() : null;
                    };

                    // Helper to get all text matching pattern
                    const findTextByPattern = (pattern) => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        let node;
                        while (node = walker.nextNode()) {
                            const match = node.textContent.match(pattern);
                            if (match) return match;
                        }
                        return null;
                    };

                    // Try to extract from page title or headers
                    const pageTitle = document.title || '';
                    const h1 = getText('h1') || getText('.title') || '';

                    // Try to find participant info - MyRace varies in structure
                    // Look for common patterns in the rendered HTML
                    const bodyText = document.body.innerText;

                    // Extract event name (usually in title or header)
                    let eventName = h1 || pageTitle.split(' - ')[0] || 'Race Results';

                    // Try to find time patterns (HH:MM:SS or H:MM:SS)
                    const timePattern = /(\d{1,2}:\d{2}:\d{2})/g;
                    const times = bodyText.match(timePattern) || [];

                    // Try to find place/position
                    const placePattern = /(?:место|place|position)[:\s]*(\d+)/i;
                    const placeMatch = bodyText.match(placePattern);

                    return {
                        eventName: eventName,
                        pageTitle: pageTitle,
                        bodyPreview: bodyText.substring(0, 2000),
                        times: times,
                        placeMatch: placeMatch ? placeMatch[1] : null,
                    };
                }
            """)

            logger.debug(f"Extracted raw data: {data}")

            # Now try to extract structured data from tables if present
            table_data = await page.evaluate("""
                () => {
                    const tables = document.querySelectorAll('table');
                    const results = [];

                    tables.forEach(table => {
                        const rows = table.querySelectorAll('tr');
                        rows.forEach(row => {
                            const cells = row.querySelectorAll('td, th');
                            const rowData = Array.from(cells).map(c => c.textContent.trim());
                            if (rowData.length > 0) {
                                results.push(rowData);
                            }
                        });
                    });

                    return results;
                }
            """)

            logger.debug(f"Table data: {table_data}")

            # Parse the extracted data
            participant_data = self._parse_extracted_data(
                data, table_data, url_parts['bib']
            )

            # Build event info
            event_name = data.get('eventName', 'Race Results')
            # Clean up event name
            if ' - ' in event_name:
                event_name = event_name.split(' - ')[0]

            event = EventInfo(
                name=event_name,
                organizer=self._extract_organizer(data),
                url=url,
            )

            return RaceCardData(participant=participant_data, event=event)

        except MyRaceParseError:
            raise
        except Exception as e:
            logger.error(f"Failed to parse MyRace URL: {e}", exc_info=True)
            raise MyRaceParseError(f"Не удалось загрузить данные: {str(e)}")

        finally:
            await page.close()

    def _parse_extracted_data(
        self,
        data: dict,
        table_data: list,
        bib: str
    ) -> ParticipantResult:
        """Parse extracted page data into ParticipantResult."""

        body_text = data.get('bodyPreview', '')

        # Try to extract name - look for patterns after bib number
        name = self._extract_name(body_text, bib)

        # Extract time - use first valid time found
        times = data.get('times', [])
        time = times[0] if times else "—"

        # Extract place
        place_str = data.get('placeMatch')
        place = int(place_str) if place_str and place_str.isdigit() else 0

        # Try to extract other fields from body text
        club = self._extract_field(body_text, ['клуб', 'club', 'team'])
        category = self._extract_field(body_text, ['категория', 'category', 'M_', 'F_', 'M30', 'F30'])
        race = self._extract_field(body_text, ['дистанция', 'distance', 'VK', 'SS', 'SR'])
        pace = self._extract_pace(body_text)

        # Extract gender from category or name patterns
        gender = None
        if category:
            if category.startswith('M') or 'муж' in category.lower():
                gender = 'M'
            elif category.startswith('F') or 'жен' in category.lower():
                gender = 'F'

        # Try to parse place_category (e.g., "1/89")
        place_category = self._extract_category_place(body_text)

        # Try to parse gender place
        place_gender = self._extract_gender_place(body_text, gender)

        return ParticipantResult(
            bib=bib,
            name=name or f"Участник #{bib}",
            time=time,
            place=place,
            club=club,
            race=race,
            category=category,
            place_category=place_category,
            place_gender=place_gender,
            gender=gender,
            pace=pace,
            checkpoints=self._extract_checkpoints(table_data)
        )

    def _extract_name(self, text: str, bib: str) -> Optional[str]:
        """Try to extract participant name from text."""
        # Look for name patterns - usually Cyrillic names
        # Pattern: capital letter followed by lowercase, space, capital + lowercase
        name_pattern = r'([А-ЯA-Z][а-яa-z]+\s+[А-ЯA-Z][а-яa-z]+)'
        matches = re.findall(name_pattern, text)

        # Filter out common non-name patterns
        skip_words = ['место', 'время', 'темп', 'категория', 'дистанция', 'race', 'results']
        for match in matches:
            lower = match.lower()
            if not any(skip in lower for skip in skip_words):
                return match

        return None

    def _extract_field(self, text: str, keywords: list) -> Optional[str]:
        """Extract field value after keyword."""
        for keyword in keywords:
            pattern = rf'{keyword}[:\s]*([^\n,]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value and len(value) < 50:  # Sanity check
                    return value
        return None

    def _extract_pace(self, text: str) -> Optional[str]:
        """Extract pace (min/km) from text."""
        # Pattern for pace like "8:28" or "8:28 мин/км"
        pattern = r'(\d{1,2}:\d{2})\s*(?:мин/км|min/km|/km)?'
        matches = re.findall(pattern, text)
        # Return last match as it's usually the pace (first is often split time)
        if matches and len(matches) > 1:
            return matches[-1]
        return matches[0] if matches else None

    def _extract_category_place(self, text: str) -> Optional[str]:
        """Extract category place like '1/89'."""
        pattern = r'(\d+)\s*/\s*(\d+)'
        match = re.search(pattern, text)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
        return None

    def _extract_gender_place(self, text: str, gender: Optional[str]) -> Optional[int]:
        """Extract absolute gender place."""
        keywords = ['абсолют', 'absolute', 'gender']
        for keyword in keywords:
            pattern = rf'{keyword}[:\s]*(\d+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_organizer(self, data: dict) -> str:
        """Extract organizer from page data."""
        # Try common patterns
        text = data.get('bodyPreview', '')
        organizer_keywords = ['организатор', 'organizer', 'organiser', 'presented by']

        for keyword in organizer_keywords:
            pattern = rf'{keyword}[:\s]*([^\n,]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:50]

        return "Unknown"

    def _extract_checkpoints(self, table_data: list) -> list:
        """Extract checkpoints from table data."""
        checkpoints = []

        for row in table_data:
            # Look for rows that look like checkpoint data
            # Typically: name/distance, time, maybe pace
            if len(row) >= 2:
                # Check if second element looks like a time
                time_pattern = r'\d{1,2}:\d{2}:\d{2}'
                for i, cell in enumerate(row):
                    if re.match(time_pattern, cell):
                        name = row[i-1] if i > 0 else f"CP{len(checkpoints)+1}"
                        pace = row[i+1] if i+1 < len(row) else None
                        checkpoints.append(Checkpoint(
                            name=name,
                            time=cell,
                            pace=pace if pace and '/' in str(pace) else None
                        ))
                        break

        return checkpoints


# Singleton for reuse
_parser_instance: Optional[MyRaceParser] = None


async def get_parser() -> MyRaceParser:
    """Get singleton parser instance."""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = MyRaceParser()
    return _parser_instance
