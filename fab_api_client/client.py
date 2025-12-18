"""Core Fab API client."""

import time
from pathlib import Path
from typing import Optional, Callable, Iterator, List
import requests

from .auth import FabAuthProvider
from .manifest_parser import ManifestParser, JsonManifestParser
from .models.domain import Library, Asset, DownloadResult, ParsedManifest
from .models.api import (
    LibrarySearchResponse,
    AssetFormatsResponse,
    DownloadInfoResponse,
)
from .exceptions import (
    FabAuthenticationError,
    FabAPIError,
    FabNotFoundError,
    FabNetworkError,
)
from .utils import sanitize_filename


class FabClient:
    """
    Generic HTTP client for marketplace APIs.
    
    This client provides Pythonic access to API endpoints via pluggable
    authentication and manifest parsing.
    
    Example:
        >>> from fab_api_client import FabClient, CookieAuthProvider, ApiEndpoints
        >>> endpoints = ApiEndpoints(...)
        >>> auth = CookieAuthProvider(cookies={...}, endpoints=endpoints)
        >>> client = FabClient(auth=auth)
        >>> library = client.get_library()
    """
    
    def __init__(
        self,
        auth: FabAuthProvider,
        manifest_parser: Optional[ManifestParser] = None,
        timeout: int = 30,
        rate_limit_delay: float = 1.5,
    ):
        """
        Initialize API client.
        
        Args:
            auth: Authentication provider with session and endpoint configuration
            manifest_parser: Optional manifest parser (defaults to JsonManifestParser)
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between API requests in seconds
        """
        self.auth = auth
        self.manifest_parser = manifest_parser or JsonManifestParser()
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        
        # Get configured session from auth provider
        self.session = auth.get_session()
        self.endpoints = auth.get_endpoints()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session."""
        self.session.close()
    
    def get_library_pages(
        self,
        sort_by: str = '-createdAt'
    ) -> Iterator[LibrarySearchResponse]:
        """
        Fetch library pages with pagination support.
        
        This is an advanced method that returns raw API response pages.
        Most users should use get_library() instead.
        
        Args:
            sort_by: Sort order (default: newest first)
        
        Yields:
            LibrarySearchResponse objects for each page
        
        Raises:
            FabAuthenticationError: If authentication fails
            FabAPIError: If API request fails
            FabNetworkError: If network error occurs
        """
        url = self.endpoints.library_search
        params = {'sort_by': sort_by}
        
        while True:
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                
                if response.status_code in (401, 403):
                    raise FabAuthenticationError(
                        f"Authentication failed (HTTP {response.status_code}). "
                        "Cookies may have expired."
                    )
                
                response.raise_for_status()
                
            except requests.exceptions.Timeout as e:
                raise FabNetworkError(f"Request timeout: {e}")
            except requests.exceptions.ConnectionError as e:
                raise FabNetworkError(f"Connection error: {e}")
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise FabNotFoundError(f"Resource not found: {url}")
                raise FabAPIError(
                    f"HTTP error {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response
                )
            
            data = response.json()
            page_response = LibrarySearchResponse.from_dict(data)
            
            yield page_response
            
            # Check if there's a next page
            if page_response.cursors and page_response.cursors.next:
                params['cursor'] = page_response.cursors.next
                time.sleep(self.rate_limit_delay)
            else:
                break
    
    def get_library(self, sort_by: str = '-createdAt') -> Library:
        """
        Fetch complete library with all assets.
        
        This method handles pagination automatically and returns all assets.
        
        Args:
            sort_by: Sort order (default: newest first)
        
        Returns:
            Library object with all assets
        
        Raises:
            FabAuthenticationError: If authentication fails
            FabAPIError: If API request fails
            FabNetworkError: If network error occurs
        """
        all_assets = []
        
        for page in self.get_library_pages(sort_by=sort_by):
            assets = page.to_assets()
            all_assets.extend(assets)
        
        return Library(assets=all_assets, total_count=len(all_assets))
    
    def _discover_file_uid(self, asset_uid: str) -> Optional[str]:
        """
        Discover file UID for an asset's Unreal Engine format.
        
        Args:
            asset_uid: Asset/entitlement UID
        
        Returns:
            File UID if found, None otherwise
        """
        url = self.endpoints.asset_formats.format(asset_uid=asset_uid)
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code in (401, 403):
                raise FabAuthenticationError(
                    f"Authentication failed (HTTP {response.status_code})"
                )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            formats_response = AssetFormatsResponse.from_api_response(data)
            return formats_response.find_unreal_file_uid()
            
        except requests.exceptions.Timeout as e:
            raise FabNetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response
            )
    
    def _get_download_info(
        self,
        asset_uid: str,
        file_uid: str,
        platform: str = 'Mac'
    ) -> Optional[DownloadInfoResponse]:
        """
        Get download info including manifest URL.
        
        Args:
            asset_uid: Asset/entitlement UID
            file_uid: File UID
            platform: Platform name
        
        Returns:
            DownloadInfoResponse if successful, None otherwise
        """
        url = self.endpoints.download_info.format(asset_uid=asset_uid, file_uid=file_uid)
        params = {'platform': platform}
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            if response.status_code in (401, 403):
                raise FabAuthenticationError(
                    f"Authentication failed (HTTP {response.status_code})"
                )
            
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            
            data = response.json()
            return DownloadInfoResponse.from_dict(data)
            
        except requests.exceptions.Timeout as e:
            raise FabNetworkError(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response
            )
    
    def download_manifest(
        self,
        asset: Asset,
        output_dir: Path,
        on_progress: Optional[Callable[[str], None]] = None
    ) -> ParsedManifest:
        """
        Download and parse manifest for a single asset.
        
        Args:
            asset: Asset to download manifest for
            output_dir: Directory to save manifest
            on_progress: Optional callback for progress updates
        
        Returns:
            ParsedManifest object
        
        Raises:
            Exception: If download or parsing fails
        """
        output_dir = Path(output_dir)
        
        # Step 1: Discover file UID
        if on_progress:
            on_progress(f"Discovering file UID for {asset.title}")
        
        file_uid = self._discover_file_uid(asset.uid)
        if not file_uid:
            raise ValueError("No Unreal Engine format found")
        
        time.sleep(self.rate_limit_delay)
        
        # Step 2: Get download info
        if on_progress:
            on_progress(f"Getting download info for {asset.title}")
        
        download_info = self._get_download_info(asset.uid, file_uid)
        if not download_info:
            raise ValueError("Download info not found")
        
        manifest_url = download_info.find_manifest_url()
        if not manifest_url:
            raise ValueError("Manifest URL not found in download info")
        
        time.sleep(self.rate_limit_delay)
        
        # Step 3: Download manifest
        if on_progress:
            on_progress(f"Downloading manifest for {asset.title}")
        
        # Download raw manifest bytes
        response = requests.get(manifest_url, timeout=60)
        response.raise_for_status()
        raw_data = response.content
        
        # Step 4: Parse manifest through parser
        if on_progress:
            on_progress(f"Parsing manifest for {asset.title}")
        
        manifest = self.manifest_parser.parse(raw_data)
        
        # Optionally save to disk
        sanitized_title = sanitize_filename(asset.title)
        output_filename = f"{sanitized_title}_{asset.uid}.manifest"
        output_path = output_dir / output_filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(raw_data)
        
        return manifest
    
    def download_manifests(
        self,
        assets: List[Asset],
        output_dir: Path,
        on_progress: Optional[Callable[[Asset, str], None]] = None
    ) -> List[ParsedManifest]:
        """
        Download and parse manifests for multiple assets.
        
        Args:
            assets: List of assets to download manifests for
            output_dir: Directory to save manifests
            on_progress: Optional callback for progress updates
        
        Returns:
            List of ParsedManifest objects
        """
        manifests = []
        
        for asset in assets:
            if on_progress:
                on_progress(asset, "starting")
            
            try:
                manifest = self.download_manifest(
                    asset,
                    output_dir,
                    on_progress=lambda msg: on_progress(asset, msg) if on_progress else None
                )
                manifests.append(manifest)
                
                if on_progress:
                    on_progress(asset, "completed")
            except Exception as e:
                if on_progress:
                    on_progress(asset, f"failed: {e}")
        
        return manifests
