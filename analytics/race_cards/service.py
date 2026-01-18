"""
High-level Race Card Service.
Combines parsing and generation for easy bot integration.
"""
import logging
from typing import Optional

from .models import RaceCardData, RaceCardOutput
from .parser import get_parser, MyRaceParser, MyRaceParseError
from .generator import get_generator, RaceCardGenerator

logger = logging.getLogger(__name__)


class RaceCardServiceError(Exception):
    """Service-level error."""
    pass


class RaceCardService:
    """
    High-level service for generating race result cards.
    Provides async interface for Telegram bot integration.
    """

    def __init__(self, parser: MyRaceParser, generator: RaceCardGenerator):
        self.parser = parser
        self.generator = generator

    @staticmethod
    def validate_url(url: str) -> tuple[bool, str]:
        """
        Validate MyRace URL without parsing.

        Returns:
            Tuple of (is_valid, error_message or bib_number)
        """
        return MyRaceParser.validate_url(url)

    async def generate_from_url(self, url: str) -> RaceCardOutput:
        """
        Generate race cards from MyRace URL.

        Args:
            url: MyRace URL with bib parameter

        Returns:
            RaceCardOutput with single_post and carousel_slides

        Raises:
            RaceCardServiceError: If parsing or generation fails
        """
        try:
            # Parse race data
            logger.info(f"Parsing race data from URL: {url}")
            race_data = await self.parser.parse_result(url)

            # Generate cards
            logger.info(f"Generating cards for {race_data.participant.name}")
            output = await self.generator.generate_all(race_data)

            logger.info(f"Successfully generated {len(output.carousel_slides) + 1} cards")
            return output

        except MyRaceParseError as e:
            logger.error(f"Parse error: {e}")
            raise RaceCardServiceError(f"Не удалось загрузить данные: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating race cards: {e}", exc_info=True)
            raise RaceCardServiceError(f"Не удалось сгенерировать карточки: {str(e)}")

    async def generate_from_data(self, data: RaceCardData) -> RaceCardOutput:
        """
        Generate race cards from pre-populated data.
        Useful for testing or manual data entry.

        Args:
            data: RaceCardData with participant and event info

        Returns:
            RaceCardOutput with all images
        """
        try:
            return await self.generator.generate_all(data)
        except Exception as e:
            logger.error(f"Error generating race cards: {e}", exc_info=True)
            raise RaceCardServiceError(f"Не удалось сгенерировать карточки: {str(e)}")

    async def close(self):
        """Close parser and generator resources."""
        await self.parser.close()
        await self.generator.close()


# Singleton service
_service_instance: Optional[RaceCardService] = None


async def get_race_card_service() -> RaceCardService:
    """Get singleton service instance."""
    global _service_instance
    if _service_instance is None:
        parser = await get_parser()
        generator = await get_generator()
        _service_instance = RaceCardService(parser, generator)
    return _service_instance
