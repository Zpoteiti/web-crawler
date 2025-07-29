"""
pacong.browser - 浏览器控制模块
提供多种浏览器控制方式：Selenium、AppleScript、Chrome DevTools Protocol
"""

from .applescript import execute_applescript, chrome_applescript_scraper
from .cdp import CDPController
from .selenium_controller import SeleniumController

__all__ = [
    'execute_applescript',
    'chrome_applescript_scraper', 
    'CDPController',
    'SeleniumController'
] 