import sys
from pathlib import Path

# Add project root to sys.path so 'backend' package is discoverable
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import uvicorn
from backend.app.config import settings

def main():
    print("=" * 60)
    print(f"  {settings.APP_NAME.upper()} — {settings.APP_TAGLINE}")
    print(f"  Version: {settings.VERSION} | Environment: {settings.ENVIRONMENT}")
    print(f"  Server URL: http://{settings.HOST}:{settings.PORT}")
    if settings.DEMO_MODE:
        print("  Demo Mode: ACTIVE (Seed & fast switch enabled)")
    print("=" * 60)

    uvicorn.run(
        "backend.app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=(settings.ENVIRONMENT == "development")
    )

if __name__ == "__main__":
    main()
