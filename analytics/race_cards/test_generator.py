"""
Test script for race card generator.
Run: python -m analytics.race_cards.test_generator
"""
import asyncio
import os
from pathlib import Path

from .models import ParticipantResult, EventInfo, RaceCardData, Checkpoint
from .generator import RaceCardGenerator


async def test_generate_cards():
    """Test card generation with sample data."""

    # Sample data - top 3 result
    participant = ParticipantResult(
        bib="320",
        name="Иван Шилов",
        club="SkyRunGroup",
        time="01:58:24",
        place=3,
        race="VK 1000",
        category="M30-39",
        place_category="1/89",
        place_gender=5,
        gender="M",
        pace="8:28",
        distance_km=5,
        elevation_gain=1000,
        start_elevation=2850,
        finish_elevation=3850,
        checkpoints=[
            Checkpoint(name="CP1", distance_km=2, time="00:38:12", pace="7:38 /км"),
            Checkpoint(name="CP2", distance_km=3.5, time="01:12:45", pace="8:38 /км"),
            Checkpoint(name="Финиш", distance_km=5, time="01:58:24", pace="11:27 /км"),
        ]
    )

    event = EventInfo(
        name="Amangeldy Race 2026",
        organizer="AthleteX",
        timing_provider="MyRace",
        date="17 января 2026"
    )

    data = RaceCardData(participant=participant, event=event)

    # Generate cards
    generator = RaceCardGenerator()

    try:
        print("Generating cards...")
        output = await generator.generate_all(data)

        # Save to files for inspection
        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)

        # Save single post
        single_path = output_dir / "single_post.png"
        with open(single_path, "wb") as f:
            f.write(output.single_post)
        print(f"Saved: {single_path}")

        # Save carousel slides
        for i, slide in enumerate(output.carousel_slides):
            slide_path = output_dir / f"carousel_slide_{i+1}.png"
            with open(slide_path, "wb") as f:
                f.write(slide)
            print(f"Saved: {slide_path}")

        print(f"\nSuccess! Generated {1 + len(output.carousel_slides)} cards")
        print(f"Output directory: {output_dir.absolute()}")

    finally:
        await generator.close()


async def test_regular_result():
    """Test with regular (non-podium) result."""

    participant = ParticipantResult(
        bib="547",
        name="Мария Козлова",
        club="Бег с удовольствием",
        time="03:12:45",
        place=156,
        race="VK 1000",
        category="F30-39",
        place_category="23/45",
        place_gender=64,
        gender="F",
        pace="13:46",
        distance_km=5,
        elevation_gain=1000,
    )

    event = EventInfo(
        name="Amangeldy Race 2026",
        organizer="AthleteX",
        timing_provider="MyRace",
    )

    data = RaceCardData(participant=participant, event=event)

    generator = RaceCardGenerator()

    try:
        print("\nGenerating regular result cards...")
        output = await generator.generate_all(data)

        output_dir = Path(__file__).parent / "test_output"
        output_dir.mkdir(exist_ok=True)

        # Save single post
        single_path = output_dir / "regular_post.png"
        with open(single_path, "wb") as f:
            f.write(output.single_post)
        print(f"Saved: {single_path}")

        print("Success!")

    finally:
        await generator.close()


if __name__ == "__main__":
    asyncio.run(test_generate_cards())
    asyncio.run(test_regular_result())
