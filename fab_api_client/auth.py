"""Authentication and endpoint configuration for Fab API client."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional
import requests


@dataclass
class ApiEndpoints:
    """Configuration for API endpoint URLs.
    
    Attributes:
        library_search: URL for library search endpoint
        asset_formats: URL template for asset formats (use {asset_uid})
        download_info: URL template for download info (use {asset_uid}, {file_uid})
    """
    library_search: str
    asset_formats: str
    download_info: str


class FabAuthProvider(ABC):
    """Abstract base class for authentication providers.
    
    Implementations must provide both session configuration and endpoint URLs.
    """
    
    @abstractmethod
    def get_session(self) -> requests.Session:
        """Return configured requests.Session with authentication.
        
        Returns:
            Configured Session object ready for API requests
        """
        pass
    
    @abstractmethod
    def get_endpoints(self) -> ApiEndpoints:
        """Return API endpoint configuration.
        
        Returns:
            ApiEndpoints with URL configuration
        """
        pass


class CookieAuthProvider(FabAuthProvider):
    """Generic cookie-based authentication provider.
    
    This is a generic implementation that requires all configuration
    to be provided explicitly - no hardcoded values.
    """
    
    def __init__(
        self,
        cookies: Dict[str, str],
        endpoints: ApiEndpoints,
        user_agent: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        verify_ssl: bool = True
    ):
        """Initialize cookie-based authentication.
        
        Args:
            cookies: Dictionary of cookies for authentication
            endpoints: API endpoint configuration
            user_agent: Optional user agent string
            headers: Optional additional headers
            verify_ssl: Whether to verify SSL certificates
        """
        self.cookies = cookies
        self.endpoints = endpoints
        self.user_agent = user_agent
        self.headers = headers or {}
        self.verify_ssl = verify_ssl
    
    def get_session(self) -> requests.Session:
        """Create and configure a requests session.
        
        Returns:
            Configured Session with cookies and headers
        """
        session = requests.Session()
        session.cookies.update(self.cookies)
        session.verify = self.verify_ssl
        
        if self.user_agent:
            session.headers['User-Agent'] = self.user_agent
        
        session.headers.update(self.headers)
        
        return session
    
    def get_endpoints(self) -> ApiEndpoints:
        """Return the configured endpoints.
        
        Returns:
            ApiEndpoints configuration
        """
        return self.endpoints
