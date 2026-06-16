PROJECT_BROWSER_MAP = {
    # desktop
    "chromium": "Chromium",
    "firefox": "Firefox",
    "webkit": "WebKit",
    "edge": "Edge",

    # mobile/tablet - map to underlying engine
    "Pixel 5": "Chromium",
    "Pixel 8 Pro": "Chromium",
    "Galaxy S24": "Chromium",
    "iPhone 13": "WebKit",
    "iPad Pro 11": "WebKit",
}

def get_browser_engine(project: str) -> str:
    """
    Returns the underlying browser engine for a given browser profile or device name.
    """
    return PROJECT_BROWSER_MAP.get(project, "Chromium")
