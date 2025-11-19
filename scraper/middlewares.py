import json
import logging

import requests
from scrapy import signals
from scrapy.http import HtmlResponse

logger = logging.getLogger(__name__)


class HeaderLoggingMiddleware:
    """Middleware to log all request headers for debugging"""

    def process_request(self, request, spider):
        """Log headers before sending request"""
        logger.info(f"\n{'='*80}\n🔍 REQUEST HEADERS for: {request.url}\n{'='*80}")
        for key, value in request.headers.items():
            logger.info(f"  {key.decode()}: {value[0].decode()}")
        logger.info(f"{'='*80}\n")
        return None

    def process_response(self, request, response, spider):
        """Log response status"""
        logger.info(f"✓ Response {response.status} for: {request.url}")
        return response

    def process_exception(self, request, exception, spider):
        """Log headers even when request fails"""
        logger.error(f"\n{'='*80}\n❌ REQUEST FAILED for: {request.url}")
        logger.error(f"Exception: {exception}\n{'='*80}")
        logger.error("Headers that were sent:")
        for key, value in request.headers.items():
            logger.error(f"  {key.decode()}: {value[0].decode()}")
        logger.error(f"{'='*80}\n")


class BrightDataMiddleware:
    """Middleware to use Bright Data API for protected sites"""

    def __init__(self):
        self.api_url = "https://api.brightdata.com/request"
        self.headers = {
            "Authorization": "Bearer 3b3bc582105d05bc9bdeb3b4ac62240ab9abd332e6b26e65ea0ed284b26247d6",
            "Content-Type": "application/json",
        }
        self.zone = "unlocker"

    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware

    def process_request(self, request, spider):
        # Only use Bright Data for specific domains
        if "booktoki" in request.url:
            logger.info(f"Using Bright Data API for: {request.url}")

            try:
                data = {
                    "zone": self.zone,
                    "url": request.url,
                    "format": "raw",
                    "render": True,
                }

                response = requests.post(
                    self.api_url,
                    json=data,
                    headers=self.headers,
                    timeout=60,
                )

                if response.status_code == 200:
                    logger.info(f"Successfully fetched via Bright Data: {request.url}")

                    # Return a Scrapy Response object
                    return HtmlResponse(
                        url=request.url,
                        status=200,
                        body=response.content,
                        encoding="utf-8",
                        request=request,
                    )
                else:
                    logger.error(
                        f"Bright Data API error: {response.status_code} - {response.text}"
                    )
                    return None

            except Exception as e:
                logger.error(f"Bright Data API exception: {e}")
                return None

        # Let other requests pass through normally
        return None

    def spider_opened(self, spider):
        logger.info(f"BrightDataMiddleware enabled for spider: {spider.name}")
