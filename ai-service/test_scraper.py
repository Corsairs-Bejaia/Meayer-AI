import asyncio
import logging
import sys

from app.services.browser_pool import browser_pool
from app.services.cnas_scraper import scrape_cnas

logging.basicConfig(level=logging.INFO, stream=sys.stdout)

async def test_scraper():
    print("Starting browser pool...")
    await browser_pool.start()
    
    test_attestation = "12345678"
    test_employer = "87654321"
    
    print(f"Testing CNAS Scraper with Attestation: {test_attestation}, Employer: {test_employer}")
    
    try:
        result = await scrape_cnas(
            attestation_number=test_attestation,
            employer_number=test_employer
        )
        print("Scraping Result:")
        import json
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        print("Stopping browser pool...")
        await browser_pool.stop()

if __name__ == "__main__":
    asyncio.run(test_scraper())
