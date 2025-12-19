#!/usr/bin/env python3
"""
Test script to verify enhanced data models parse API responses correctly.
"""

from fab_api_client.models.api import LibrarySearchResponse
from fab_api_client.models.domain import Asset, Listing, License, Seller

# Sample API response data matching the structure you provided
sample_response = {
    "results": [
        {
            "capabilities": {
                "addByVerse": False,
                "requestDownloadUrl": True
            },
            "createdAt": "2025-12-17T02:16:49.664790+00:00",
            "licenses": [
                {
                    "name": "Standard License",
                    "slug": "standard",
                    "url": "/eula"
                }
            ],
            "listing": {
                "assetFormats": [
                    {
                        "assetFormatType": {
                            "code": "unreal-engine",
                            "icon": "unreal-engine",
                            "name": "Unreal Engine",
                            "groupName": "Game Engine Formats"
                        },
                        "technicalSpecs": {
                            "technicalDetails": "<p><strong>Number of Meshes</strong>: 0</p>",
                            "unrealEngineEngineVersions": [
                                "UE_5.4",
                                "UE_5.3"
                            ],
                            "unrealEngineTargetPlatforms": [
                                "Windows",
                                "Mac"
                            ],
                            "unrealEngineDistributionMethod": "asset_pack"
                        }
                    }
                ],
                "isMature": True,
                "lastUpdatedAt": "2025-07-03T23:18:09.319385Z",
                "licenses": [
                    {
                        "type": "",
                        "isCc0": False,
                        "name": "Personal",
                        "priceTier": "45da1a2f292a46c78dab0c98c5181e9a_USD_999_1701881383878",
                        "uid": "eec3bdd5-ba7a-45a8-b15d-67462b9630f6"
                    }
                ],
                "listingType": "3d-model",
                "tags": [
                    {
                        "slug": "postapocalyptic",
                        "uid": "0f89b929-9f95-43cf-8255-d9f5cf2139ad"
                    },
                    {
                        "slug": "blood",
                        "uid": "1b393276-dadb-4c1f-b863-bbb99e64833c"
                    }
                ],
                "title": "Decals VOL.3 - Blood",
                "uid": "bbcff104-9ca4-400f-b529-c0cdccf7bff6",
                "user": {
                    "avatars": [],
                    "coverImageUrl": "https://cdn1.epicgames.com/fab/seller/cover/0f5788bc.jpg",
                    "isSeller": True,
                    "profileImageUrl": "https://cdn1.epicgames.com/fab/seller/profile/a4422bc9.png",
                    "sellerName": "Dekogon Studios",
                    "sellerId": "o-efb24a1bbc44bea38a4f0b91a0ad66",
                    "uid": "0e84df24-fdee-4f1b-bab8-3d8db79d3801"
                }
            },
            "status": "approved",
            "uid": "253b7c44-2758-4608-8186-679c80567154"
        }
    ],
    "cursors": {"next": None, "previous": None},
    "next": None,
    "aggregations": None
}


def test_parsing():
    """Test that the enhanced models parse the API response correctly."""
    print("🧪 Testing Enhanced Data Models")
    print("=" * 60)
    print()
    
    # Parse the API response
    response = LibrarySearchResponse.from_dict(sample_response)
    assets = response.to_assets()
    
    assert len(assets) == 1, f"Expected 1 asset, got {len(assets)}"
    asset = assets[0]
    
    # Test Asset fields
    print("✓ Asset parsed successfully")
    print(f"  - UID: {asset.uid}")
    print(f"  - Title: {asset.title}")
    print(f"  - Status: {asset.status}")
    print(f"  - Created at: {asset.created_at}")
    
    # Test Capabilities
    assert asset.capabilities is not None, "Capabilities should not be None"
    print(f"  - Capabilities:")
    print(f"    - Add by Verse: {asset.capabilities.add_by_verse}")
    print(f"    - Request Download URL: {asset.capabilities.request_download_url}")
    
    # Test Granted Licenses
    assert len(asset.granted_licenses) == 1, f"Expected 1 granted license, got {len(asset.granted_licenses)}"
    print(f"  - Granted Licenses: {len(asset.granted_licenses)}")
    print(f"    - {asset.granted_licenses[0].name} ({asset.granted_licenses[0].slug})")
    
    # Test Listing
    assert asset.listing is not None, "Listing should not be None"
    listing = asset.listing
    print()
    print("✓ Listing parsed successfully")
    print(f"  - UID: {listing.uid}")
    print(f"  - Title: {listing.title}")
    print(f"  - Listing Type: {listing.listing_type}")
    print(f"  - Is Mature: {listing.is_mature}")
    print(f"  - Last Updated: {listing.last_updated_at}")
    
    # Test Tags (should be strings)
    assert len(listing.tags) == 2, f"Expected 2 tags, got {len(listing.tags)}"
    assert isinstance(listing.tags[0], str), "Tags should be strings"
    print(f"  - Tags: {', '.join(listing.tags)}")
    
    # Test Listing Licenses
    assert len(listing.licenses) == 1, f"Expected 1 listing license, got {len(listing.licenses)}"
    print(f"  - Licenses: {len(listing.licenses)}")
    lic = listing.licenses[0]
    print(f"    - {lic.name} (UID: {lic.uid})")
    print(f"    - Price Tier: {lic.price_tier}")
    print(f"    - CC0: {lic.is_cc0}")
    
    # Test Seller
    assert listing.seller is not None, "Seller should not be None"
    seller = listing.seller
    print(f"  - Seller:")
    print(f"    - Name: {seller.seller_name}")
    print(f"    - ID: {seller.seller_id}")
    print(f"    - Profile Image: {seller.profile_image_url}")
    
    # Test Asset Formats
    assert len(listing.asset_formats) == 1, f"Expected 1 asset format, got {len(listing.asset_formats)}"
    fmt = listing.asset_formats[0]
    print(f"  - Asset Formats: {len(listing.asset_formats)}")
    print(f"    - Type: {fmt.asset_format_type.name} ({fmt.asset_format_type.code})")
    print(f"    - Group: {fmt.asset_format_type.group_name}")
    
    assert fmt.technical_specs is not None, "Technical specs should not be None"
    specs = fmt.technical_specs
    print(f"    - Engine Versions: {', '.join(specs.unreal_engine_engine_versions)}")
    print(f"    - Platforms: {', '.join(specs.unreal_engine_target_platforms)}")
    print(f"    - Distribution: {specs.unreal_engine_distribution_method}")
    
    print()
    print("=" * 60)
    print("✅ All tests passed!")
    print()


if __name__ == "__main__":
    test_parsing()
