"""Core Fab API client."""

import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Callable, Optional, Union

import requests
from asset_marketplace_core import DownloadResult as CoreDownloadResult
from asset_marketplace_core import (
    MarketplaceClient,
    ProgressCallback,
    safe_create_directory,
    sanitize_filename,
    validate_url,
)

from ..auth import FabAuthProvider
from ..exceptions import (
    FabAPIError,
    FabAuthenticationError,
    FabNetworkError,
    FabNotFoundError,
)
from ..manifest_parser import JsonManifestParser, ManifestParser
from ..models.api import (
    AssetFormatsResponse,
    DownloadInfoResponse,
    LibrarySearchResponse,
)
from ..models.domain import Asset, Library, ManifestDownloadResult


class FabClient(MarketplaceClient):
    """
    Fab marketplace API client extending MarketplaceClient.

    This client provides Pythonic access to Fab API endpoints via pluggable
    authentication and manifest parsing. Extends the core MarketplaceClient
    for multi-platform compatibility.

    Example:
        >>> from fab_api_client import FabClient, CookieAuthProvider, FabEndpoints
        >>> endpoints = FabEndpoints(base_url="https://...", ...)
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
    ) -> None:
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

    # Context manager methods inherited from MarketplaceClient

    def get_collection(self, **kwargs: Any) -> Library:
        """Retrieve asset collection (implements core MarketplaceClient interface).

        This is an alias for get_library() to implement the core interface.

        Args:
            **kwargs: Query parameters (e.g., sort_by)

        Returns:
            Library collection of assets

        Raises:
            FabAuthenticationError: If authentication fails
            FabAPIError: If API request fails
            FabNetworkError: If network error occurs
        """
        return self.get_library(**kwargs)

    def get_asset(self, asset_uid: str) -> Asset:
        """Retrieve a specific asset by UID.

        Implements core MarketplaceClient interface.

        Args:
            asset_uid: Unique identifier for the asset

        Returns:
            Asset details

        Raises:
            FabNotFoundError: If asset doesn't exist
            FabAuthenticationError: If authentication fails
            FabAPIError: If API request fails
            FabNetworkError: If network error occurs
        """
        # Fetch the full library and find the asset
        # Note: Fab API doesn't have a single-asset endpoint,
        # so we fetch the library and filter
        library = self.get_library()
        asset = library.find_by_uid(asset_uid)

        if asset is None:
            raise FabNotFoundError(f"Asset with UID '{asset_uid}' not found")

        # Type check: ensure we're returning Asset, not BaseAsset
        if not isinstance(asset, Asset):
            raise TypeError(f"Expected Asset, got {type(asset).__name__}")

        return asset

    def download_asset(
        self,
        asset_uid: str,
        output_dir: Union[str, Path],
        progress_callback: Optional[ProgressCallback] = None,
        **kwargs: Any,
    ) -> CoreDownloadResult:
        """Download asset manifest (implements core MarketplaceClient interface).

        Downloads the manifest file for the specified asset.

        Args:
            asset_uid: Unique identifier for the asset to download
            output_dir: Directory where manifest should be saved
            progress_callback: Optional callback for progress updates
            **kwargs: Additional download parameters (unused)

        Returns:
            CoreDownloadResult with download details

        Raises:
            FabNotFoundError: If asset doesn't exist
            FabValidationError: If output_dir is invalid
            FabAPIError: If download fails
        """
        output_path = Path(output_dir)

        # Ensure output directory exists and is safe
        safe_create_directory(output_path)

        # Get the asset
        asset = self.get_asset(asset_uid)

        if progress_callback:
            progress_callback.on_start(None)

        try:
            # Download manifest using existing method
            def simple_progress(msg: str) -> None:
                if progress_callback:
                    # Simple progress reporting without byte counts
                    progress_callback.on_progress(0, None)

            manifest_result = self.download_manifest(
                asset, output_path, on_progress=simple_progress
            )

            if progress_callback:
                progress_callback.on_complete()

            # Convert to core DownloadResult
            if manifest_result.success and manifest_result.file_path:
                return CoreDownloadResult(
                    success=True,
                    asset_uid=asset_uid,
                    files=[str(manifest_result.file_path)],
                    metadata={"size_bytes": manifest_result.size or 0},
                )
            else:
                return CoreDownloadResult(
                    success=False,
                    asset_uid=asset_uid,
                    files=[],
                    error=manifest_result.error or "Unknown error",
                )

        except Exception as e:
            if progress_callback:
                progress_callback.on_error(e)

            return CoreDownloadResult(
                success=False, asset_uid=asset_uid, files=[], error=str(e)
            )

    def close(self) -> None:
        """Close the client and clean up resources (implements core interface).

        Closes the HTTP session to free up resources.
        """
        if hasattr(self, "session"):
            self.session.close()

    def get_library_pages(
        self, sort_by: str = "-createdAt"
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
        params = {"sort_by": sort_by}

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
                raise FabNetworkError(f"Request timeout: {e}") from e
            except requests.exceptions.ConnectionError as e:
                raise FabNetworkError(f"Connection error: {e}") from e
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    raise FabNotFoundError(f"Resource not found: {url}") from e
                raise FabAPIError(
                    f"HTTP error {e.response.status_code}",
                    status_code=e.response.status_code,
                    response=e.response,
                ) from e

            data = response.json()
            page_response = LibrarySearchResponse.from_dict(data)

            yield page_response

            # Check if there's a next page
            if page_response.cursors and page_response.cursors.next:
                params["cursor"] = page_response.cursors.next
                time.sleep(self.rate_limit_delay)
            else:
                break

    def get_library(self, sort_by: str = "-createdAt") -> Library:
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
            raise FabNetworkError(f"Request timeout: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}") from e
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response,
            ) from e

    def _get_download_info(
        self, asset_uid: str, file_uid: str, platform: str = "Mac"
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
        url = self.endpoints.download_info.format(
            asset_uid=asset_uid, file_uid=file_uid
        )
        params = {"platform": platform}

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
            raise FabNetworkError(f"Request timeout: {e}") from e
        except requests.exceptions.ConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}") from e
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.response.status_code}",
                status_code=e.response.status_code,
                response=e.response,
            ) from e

    def download_manifest(
        self,
        asset: Asset,
        output_dir: Path,
        on_progress: Optional[Callable[[str], None]] = None,
    ) -> ManifestDownloadResult:
        """
        Download manifest for a single asset.

        Args:
            asset: Asset to download manifest for
            output_dir: Directory to save manifest
            on_progress: Optional callback for progress updates

        Returns:
            ManifestDownloadResult with download details

        Raises:
            FabAPIError: If download or parsing fails
        """
        output_dir = Path(output_dir)

        try:
            # Ensure output directory exists and is safe
            safe_create_directory(output_dir)

            # Step 1: Discover file UID
            if on_progress:
                on_progress(f"Discovering file UID for {asset.title}")

            file_uid = self._discover_file_uid(asset.uid)
            if not file_uid:
                return ManifestDownloadResult(
                    success=False, error="No Unreal Engine format found"
                )

            time.sleep(self.rate_limit_delay)

            # Step 2: Get download info
            if on_progress:
                on_progress(f"Getting download info for {asset.title}")

            download_info = self._get_download_info(asset.uid, file_uid)
            if not download_info:
                return ManifestDownloadResult(
                    success=False, error="Download info not found"
                )

            manifest_url = download_info.find_manifest_url()
            if not manifest_url:
                return ManifestDownloadResult(
                    success=False, error="Manifest URL not found in download info"
                )

            # Security: Validate URL
            if not validate_url(manifest_url):
                return ManifestDownloadResult(
                    success=False, error=f"Invalid manifest URL: {manifest_url}"
                )

            time.sleep(self.rate_limit_delay)

            # Step 3: Download manifest
            if on_progress:
                on_progress(f"Downloading manifest for {asset.title}")

            # Download raw manifest bytes
            response = requests.get(manifest_url, timeout=60)
            response.raise_for_status()
            raw_data = response.content

            # Step 4: Save to disk with sanitized filename
            sanitized_title = sanitize_filename(asset.title)
            output_filename = f"{sanitized_title}_{asset.uid}.manifest"
            output_path = output_dir / output_filename

            with open(output_path, "wb") as f:
                f.write(raw_data)

            return ManifestDownloadResult(
                success=True,
                file_path=output_path,
                size=len(raw_data),
            )

        except Exception as e:
            return ManifestDownloadResult(success=False, error=str(e))

    def download_manifests(
        self,
        assets: list[Asset],
        output_dir: Path,
        on_progress: Optional[Callable[[Asset, str], None]] = None,
    ) -> list[ManifestDownloadResult]:
        """
        Download manifests for multiple assets.

        Args:
            assets: List of assets to download manifests for
            output_dir: Directory to save manifests
            on_progress: Optional callback for progress updates

        Returns:
            List of ManifestDownloadResult objects
        """
        results = []

        for asset in assets:
            if on_progress:
                on_progress(asset, "starting")

            # Fix B023: Bind loop variable in lambda
            def make_progress_callback(
                current_asset: Asset,
            ) -> Optional[Callable[[str], None]]:
                if on_progress:
                    return lambda msg: on_progress(current_asset, msg)
                return None

            result = self.download_manifest(
                asset,
                output_dir,
                on_progress=make_progress_callback(asset),
            )
            results.append(result)

            if on_progress:
                status = "completed" if result.success else f"failed: {result.error}"
                on_progress(asset, status)

        return results
