import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from services.enhanced_downloader import EnhancedMediaDownloader

async def main():
    try:
        print("Initializing EnhancedMediaDownloader...")
        async with EnhancedMediaDownloader() as downloader:
            print("Downloader initialized successfully.")
            # We won't download anything to avoid network calls/timeouts in this check, 
            # just verifying the class structure and imports.
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
