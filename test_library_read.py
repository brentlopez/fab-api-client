#!/usr/bin/env python3
"""
Test script to verify reading FAB library contents.

This script uses the fab-egl-adapter to:
1. Extract cookies from Epic Games Launcher (automated via mitmproxy)
2. Authenticate with Fab API
3. Fetch and display library contents
"""
import sys
import os

# Add fab-egl-adapter to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../fab-egl-adapter'))

try:
    from extractors import MitmproxyExtractor
    from auth_providers import EpicGamesLauncherAuth
    from manifest_parsers import EpicManifestParser
except ImportError as e:
    print(f"❌ Error importing fab-egl-adapter: {e}")
    print("\nMake sure fab-egl-adapter is installed:")
    print("  cd ~/Projects/fab-egl-adapter")
    print("  pip install -e .")
    sys.exit(1)

try:
    from fab_api_client import FabClient
except ImportError as e:
    print(f"❌ Error importing fab-api-client: {e}")
    print("\nMake sure fab-api-client is installed:")
    print("  cd ~/Projects/fab-api-client")
    print("  pip install -e .")
    sys.exit(1)


def main():
    print("🧪 FAB Library Read Test")
    print("=" * 60)
    print()
    
    # Step 1: Extract cookies
    print("📋 Step 1: Extract cookies from Epic Games Launcher")
    print("   This will:")
    print("   - Install mitmproxy certificate (if needed)")
    print("   - Enable system proxy")
    print("   - Launch Epic Games Launcher")
    print("   - Capture cookies from www.fab.com")
    print("   - Clean up")
    print()
    
    # Use context manager to ensure cleanup even on interrupt
    try:
        with MitmproxyExtractor(timeout=30) as extractor:
            print("✅ MitmproxyExtractor initialized")
            
            # Extract cookies and keep proxy running for subsequent requests
            cookies = extractor.capture_cookies(
                auto_install_cert=True,
                keep_alive=True  # Keep proxy running!
            )
            
            print(f"✅ Captured {len(cookies)} cookies")
            print()
            
            # Continue with rest of test inside context manager
            _run_library_test(cookies, extractor)
            
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        return
    except Exception as e:
        print(f"❌ Cookie extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return


def _run_library_test(cookies: dict, extractor):
    """Run the library test with captured cookies."""
    # Ensure we're still in the context manager and proxy is running
    if not extractor.is_running():
        print("❌ Proxy is not running!")
        return
    
    # Step 2: Create auth provider
    print("📋 Step 2: Initialize authentication")
    try:
        # Disable SSL verification since we're using mitmproxy
        auth = EpicGamesLauncherAuth(cookies, verify_ssl=False)
        print("✅ EpicGamesLauncherAuth initialized")
        print()
    except Exception as e:
        print(f"❌ Auth initialization failed: {e}")
        raise
    
    # Step 3: Create manifest parser
    print("📋 Step 3: Initialize manifest parser")
    try:
        parser = EpicManifestParser()
        print("✅ EpicManifestParser initialized")
        print()
    except Exception as e:
        print(f"❌ Parser initialization failed: {e}")
        raise
    
    # Step 4: Create client and fetch library
    print("📋 Step 4: Fetch library from Fab API")
    print(f"   🔄 Proxy is running - all requests go through mitmproxy")
    print()
    
    with FabClient(auth=auth, manifest_parser=parser) as client:
        print("   Fetching library...")
        library = client.get_library()
        
        print(f"✅ Library fetched: {len(library.assets)} assets")
        print()
        
        # Display results
        print("=" * 60)
        print("✅ TEST SUCCESSFUL!")
        print("=" * 60)
        print()
        print(f"📚 Your FAB Library contains {len(library.assets)} assets")
        print()
        
        # Show first 5 assets
        print("📋 Sample assets:")
        for i, asset in enumerate(library.assets[:5], 1):
            print(f"   {i}. {asset.title}")
            print(f"      UID: {asset.uid}")
            print()
        
        if len(library.assets) > 5:
            print(f"   ... and {len(library.assets) - 5} more")
            print()
        
        # Offer to filter
        print("🔍 Library filtering examples:")
        print("   # Find assets by keyword")
        print("   filtered = library.filter(lambda a: 'keyword' in a.title.lower())")
        print()
        print("   # Find specific asset by UID")
        print("   asset = library.find_by_uid('asset-uid-here')")
        print()


def main_manual():
    """Manual mode using environment variables for cookies."""
    print("🧪 FAB Library Read Test (Manual Mode)")
    print("=" * 60)
    print()
    
    # Get cookies from environment
    fab_sessionid = os.getenv('FAB_SESSIONID')
    fab_csrftoken = os.getenv('FAB_CSRFTOKEN')
    
    if not fab_sessionid or not fab_csrftoken:
        print("❌ Error: Required environment variables not set")
        print()
        print("Required variables:")
        print("  FAB_SESSIONID - Your fab_sessionid cookie")
        print("  FAB_CSRFTOKEN - Your fab_csrftoken cookie")
        print()
        print("Usage:")
        print("  export FAB_SESSIONID='xxx'")
        print("  export FAB_CSRFTOKEN='yyy'")
        print("  python3 test_library_read.py --manual")
        sys.exit(1)
    
    cookies = {
        'fab_sessionid': fab_sessionid,
        'fab_csrftoken': fab_csrftoken,
    }
    
    # Optional cookies
    if os.getenv('CF_CLEARANCE'):
        cookies['cf_clearance'] = os.getenv('CF_CLEARANCE')
    if os.getenv('CF_BM'):
        cookies['__cf_bm'] = os.getenv('CF_BM')
    
    print(f"✅ Loaded {len(cookies)} cookies from environment")
    print()
    
    # Create auth provider
    print("📋 Initializing authentication...")
    try:
        auth = EpicGamesLauncherAuth(cookies, verify_ssl=True)
        print("✅ EpicGamesLauncherAuth initialized")
        print()
    except Exception as e:
        print(f"❌ Auth initialization failed: {e}")
        return
    
    # Create manifest parser
    parser = EpicManifestParser()
    
    # Fetch library
    print("📋 Fetching library from Fab API...")
    try:
        with FabClient(auth=auth, manifest_parser=parser) as client:
            library = client.get_library()
            
            print(f"✅ Library fetched: {len(library.assets)} assets")
            print()
            
            # Display results
            print("=" * 60)
            print("✅ TEST SUCCESSFUL!")
            print("=" * 60)
            print()
            print(f"📚 Your FAB Library contains {len(library.assets)} assets")
            print()
            
            # Show first 5 assets
            print("📋 Sample assets:")
            for i, asset in enumerate(library.assets[:5], 1):
                print(f"   {i}. {asset.title}")
                print(f"      UID: {asset.uid}")
                print()
            
            if len(library.assets) > 5:
                print(f"   ... and {len(library.assets) - 5} more")
            
    except Exception as e:
        print(f"❌ Library fetch failed: {e}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--manual':
        main_manual()
    else:
        main()
