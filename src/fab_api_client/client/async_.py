"""Asynchronous Fab API client."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, Callable, Optional, Union

import aiohttp
from asset_marketplace_core import (
    AsyncMarketplaceClient,
    safe_create_directory,
    sanitize_filename,
    validate_url,
)
from asset_marketplace_core import DownloadResult as CoreDownloadResult

from ..auth import AsyncCookieAuthProvider, FabEndpoints
from ..exceptions import (
    FabAPIError,
    FabAuthenticationError,
    FabNetworkError,
    FabNotFoundError,
)
from ..models.api import (
    AssetFormatsResponse,
    DownloadInfoResponse,
    LibrarySearchResponse,
)
from ..models.domain import Asset, Library, ManifestDownloadResult


class FabAsyncClient(AsyncMarketplaceClient):
    """
    Asynchronous Fab marketplace API client extending AsyncMarketplaceClient.

    This client provides async/await access to Fab API endpoints via pluggable
    authentication. Enables high-performance concurrent operations.

    Example:
        >>> async with FabAsyncClient(auth=async_auth) as client:
        ...     # Concurrent operations
        ...     results = await asyncio.gather(
        ...         client.get_collection(),
        ...         client.get_collection(sort_by="recent")
        ...     )
    """

    def __init__(
        self,
        auth: AsyncCookieAuthProvider,
        timeout: int = 30,
        rate_limit_delay: float = 1.5,
    ) -> None:
        """
        Initialize async API client.

        Args:
            auth: Async authentication provider with session and endpoint configuration
            timeout: Request timeout in seconds
            rate_limit_delay: Delay between API requests in seconds
        """
        self.auth = auth
        self.timeout = timeout
        self.rate_limit_delay = rate_limit_delay
        self._session: Optional[aiohttp.ClientSession] = None
        self.endpoints: FabEndpoints = auth.get_endpoints()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get aiohttp session from auth provider."""
        if self._session is None:
            self._session = await self.auth.get_session()
        return self._session

    async def get_collection(self, **kwargs: Any) -> Library:
        """Retrieve asset collection (implements core AsyncMarketplaceClient interface).

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
        return await self.get_library(**kwargs)

    async def get_asset(self, asset_uid: str) -> Asset:
        """Retrieve a specific asset by UID.

        Implements core AsyncMarketplaceClient interface.

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
        library = await self.get_library()
        asset = library.find_by_uid(asset_uid)

        if asset is None:
            raise FabNotFoundError(f"Asset with UID '{asset_uid}' not found")

        if not isinstance(asset, Asset):
            raise TypeError(f"Expected Asset, got {type(asset).__name__}")

        return asset

    async def download_asset(
        self,
        asset_uid: str,
        output_dir: Union[str, Path],
        progress_callback: Optional[Any] = None,
        **kwargs: Any,
    ) -> CoreDownloadResult:
        """Download asset manifest (implements core AsyncMarketplaceClient interface).

        Downloads the manifest file for the specified asset.

        Args:
            asset_uid: Unique identifier for the asset to download
            output_dir: Directory where manifest should be saved
            progress_callback: Optional async callback for progress updates
            **kwargs: Additional download parameters (unused)

        Returns:
            CoreDownloadResult with download details

        Raises:
            FabNotFoundError: If asset doesn't exist
            FabAPIError: If download fails
        """
        output_path = Path(output_dir)
        safe_create_directory(output_path)

        asset = await self.get_asset(asset_uid)

        if progress_callback:
            if hasattr(progress_callback, "on_start"):
                await progress_callback.on_start(None)

        try:

            def simple_progress(msg: str) -> None:
                # Simple sync progress for internal use
                pass

            manifest_result = await self.download_manifest(
                asset, output_path, on_progress=simple_progress
            )

            if progress_callback:
                if hasattr(progress_callback, "on_complete"):
                    await progress_callback.on_complete()

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
                if hasattr(progress_callback, "on_error"):
                    await progress_callback.on_error(e)

            return CoreDownloadResult(
                success=False, asset_uid=asset_uid, files=[], error=str(e)
            )

    async def close(self) -> None:
        """Close the client and clean up resources (implements core interface).

        Closes the authentication provider and cleans up sessions.
        """
        await self.auth.close()
        self._session = None

    async def get_library_pages(
        self, sort_by: str = "-createdAt"
    ) -> AsyncIterator[LibrarySearchResponse]:
        """
        Fetch library pages with pagination support (async generator).

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
        session = await self._get_session()
        url = self.endpoints.library_search
        params = {"sort_by": sort_by}

        while True:
            try:
                async with session.get(
                    url, params=params, timeout=self.timeout
                ) as response:
                    if response.status in (401, 403):
                        raise FabAuthenticationError(
                            f"Authentication failed (HTTP {response.status}). "
                            "Cookies may have expired."
                        )

                    response.raise_for_status()
                    data = await response.json()

            except asyncio.TimeoutError as e:
                raise FabNetworkError(f"Request timeout: {e}") from e
            except aiohttp.ClientConnectionError as e:
                raise FabNetworkError(f"Connection error: {e}") from e
            except aiohttp.ClientResponseError as e:
                if e.status == 404:
                    raise FabNotFoundError(f"Resource not found: {url}") from e
                raise FabAPIError(
                    f"HTTP error {e.status}",
                    status_code=e.status,
                    response=None,
                ) from e

            page_response = LibrarySearchResponse.from_dict(data)
            yield page_response

            # Check if there's a next page
            if page_response.cursors and page_response.cursors.next:
                params["cursor"] = page_response.cursors.next
                await asyncio.sleep(self.rate_limit_delay)
            else:
                break

    async def get_library(self, sort_by: str = "-createdAt") -> Library:
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

        async for page in self.get_library_pages(sort_by=sort_by):
            assets = page.to_assets()
            all_assets.extend(assets)

        return Library(assets=all_assets, total_count=len(all_assets))

    async def _discover_file_uid(self, asset_uid: str) -> Optional[str]:
        """
        Discover file UID for an asset's Unreal Engine format.

        Args:
            asset_uid: Asset/entitlement UID

        Returns:
            File UID if found, None otherwise
        """
        session = await self._get_session()
        url = self.endpoints.asset_formats.format(asset_uid=asset_uid)

        try:
            async with session.get(url, timeout=self.timeout) as response:
                if response.status in (401, 403):
                    raise FabAuthenticationError(
                        f"Authentication failed (HTTP {response.status})"
                    )

                if response.status == 404:
                    return None

                response.raise_for_status()
                data = await response.json()
                formats_response = AssetFormatsResponse.from_api_response(data)
                return formats_response.find_unreal_file_uid()

        except asyncio.TimeoutError as e:
            raise FabNetworkError(f"Request timeout: {e}") from e
        except aiohttp.ClientConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.status}",
                status_code=e.status,
                response=None,
            ) from e

    async def _get_download_info(
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
        session = await self._get_session()
        url = self.endpoints.download_info.format(
            asset_uid=asset_uid, file_uid=file_uid
        )
        params = {"platform": platform}

        try:
            async with session.get(
                url, params=params, timeout=self.timeout
            ) as response:
                if response.status in (401, 403):
                    raise FabAuthenticationError(
                        f"Authentication failed (HTTP {response.status})"
                    )

                if response.status == 404:
                    return None

                response.raise_for_status()
                data = await response.json()
                return DownloadInfoResponse.from_dict(data)

        except asyncio.TimeoutError as e:
            raise FabNetworkError(f"Request timeout: {e}") from e
        except aiohttp.ClientConnectionError as e:
            raise FabNetworkError(f"Connection error: {e}") from e
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                return None
            raise FabAPIError(
                f"HTTP error {e.status}",
                status_code=e.status,
                response=None,
            ) from e

    async def download_manifest(
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
            safe_create_directory(output_dir)

            # Step 1: Discover file UID
            if on_progress:
                on_progress(f"Discovering file UID for {asset.title}")

            file_uid = await self._discover_file_uid(asset.uid)
            if not file_uid:
                return ManifestDownloadResult(
                    success=False, error="No Unreal Engine format found"
                )

            await asyncio.sleep(self.rate_limit_delay)

            # Step 2: Get download info
            if on_progress:
                on_progress(f"Getting download info for {asset.title}")

            download_info = await self._get_download_info(asset.uid, file_uid)
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

            await asyncio.sleep(self.rate_limit_delay)

            # Step 3: Download manifest
            if on_progress:
                on_progress(f"Downloading manifest for {asset.title}")

            session = await self._get_session()
            async with session.get(manifest_url, timeout=60) as response:
                response.raise_for_status()
                raw_data = await response.read()

            # Step 4: Save to disk with sanitized filename
            sanitized_title = sanitize_filename(asset.title)
            output_filename = f"{sanitized_title}_{asset.uid}.manifest"
            output_path = output_dir / output_filename

            # Use asyncio to write file without blocking
            await asyncio.to_thread(output_path.write_bytes, raw_data)

            return ManifestDownloadResult(
                success=True,
                file_path=output_path,
                size=len(raw_data),
            )

        except Exception as e:
            return ManifestDownloadResult(success=False, error=str(e))

    async def download_manifests(
        self,
        assets: list[Asset],
        output_dir: Path,
        on_progress: Optional[Callable[[Asset, str], None]] = None,
    ) -> list[ManifestDownloadResult]:
        """
        Download manifests for multiple assets concurrently.

        Args:
            assets: List of assets to download manifests for
            output_dir: Directory to save manifests
            on_progress: Optional callback for progress updates

        Returns:
            List of ManifestDownloadResult objects
        """
        tasks = []

        for asset in assets:
            if on_progress:
                on_progress(asset, "starting")

            # Create task for concurrent download
            task = self._download_manifest_with_progress(asset, output_dir, on_progress)
            tasks.append(task)

        # Execute all downloads concurrently
        results = await asyncio.gather(*tasks, return_exceptions=False)
        return list(results)

    async def _download_manifest_with_progress(
        self,
        asset: Asset,
        output_dir: Path,
        on_progress: Optional[Callable[[Asset, str], None]] = None,
    ) -> ManifestDownloadResult:
        """Helper method for concurrent manifest downloads with progress."""

        def make_progress_callback(
            current_asset: Asset,
        ) -> Optional[Callable[[str], None]]:
            if on_progress:
                return lambda msg: on_progress(current_asset, msg)
            return None

        result = await self.download_manifest(
            asset,
            output_dir,
            on_progress=make_progress_callback(asset),
        )

        if on_progress:
            status = "completed" if result.success else f"failed: {result.error}"
            on_progress(asset, status)

        return result
