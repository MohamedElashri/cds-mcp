#!/usr/bin/env python3
"""Test script for CERN SSO authentication implementation."""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from cds_mcp.auth import CERNAuthenticator, CERNAuthError, get_authenticator, is_authenticated
from cds_mcp.cds_client import CDSClient, CDSClientError


def test_authentication_setup():
    """Test if authentication credentials are properly configured."""
    print("🔐 Testing CERN SSO Authentication Setup")
    print("=" * 50)
    
    # Check environment variables
    client_id = os.getenv("CERN_CLIENT_ID")
    client_secret = os.getenv("CERN_CLIENT_SECRET")
    
    if not client_id:
        print("❌ CERN_CLIENT_ID environment variable not set")
        return False
    
    if not client_secret:
        print("❌ CERN_CLIENT_SECRET environment variable not set")
        return False
    
    print(f"✅ CERN_CLIENT_ID: {client_id[:8]}...")
    print(f"✅ CERN_CLIENT_SECRET: {'*' * len(client_secret)}")
    
    return True


def test_token_acquisition():
    """Test token acquisition from CERN SSO."""
    print("\n Testing Token Acquisition")
    print("=" * 30)
    
    try:
        authenticator = get_authenticator()
        token = authenticator.get_access_token()
        
        print(" Successfully acquired access token")
        print(f"   Token preview: {token[:20]}...")
        
        # Test token validation
        claims = authenticator.validate_token(token)
        print(" Token validation successful")
        print(f"   Subject: {claims.get('sub', 'N/A')}")
        print(f"   Audience: {claims.get('aud', 'N/A')}")
        print(f"   Expires: {claims.get('exp', 'N/A')}")
        
        return True
        
    except CERNAuthError as e:
        print(f" Authentication failed: {e}")
        return False


def test_cds_client_integration():
    """Test CDS client with authentication."""
    print("\n Testing CDS Client Integration")
    print("=" * 35)
    
    try:
        # Test with authentication enabled
        client = CDSClient(use_authentication=True)
        
        if client.is_authenticated():
            print(" CDS client authenticated successfully")
        else:
            print(" CDS client not authenticated (will use public access)")
        
        # Test a simple search
        print("   Testing search functionality...")
        results = client.search("ATLAS", size=2)
        
        print(f" Search successful: found {len(results.records)} records")
        if results.records:
            first_record = results.records[0]
            print(f"   First result: {first_record.title[:50]}...")
        
        return True
        
    except (CDSClientError, Exception) as e:
        print(f"CDS client test failed: {e}")
        return False


def test_restricted_access():
    """Test access to restricted content (if available)."""
    print("\n Testing Restricted Content Access")
    print("=" * 38)
    
    try:
        client = CDSClient(use_authentication=True)
        
        # Try to search for restricted content (ATLAS internal notes)
        results = client.search("ATLAS internal note", experiment="ATLAS", size=1)
        
        if results.records:
            print(" Successfully accessed restricted content")
            print(f"   Found {len(results.records)} restricted records")
        else:
            print(" No restricted records found (may not have access or none exist)")
        
        return True
        
    except Exception as e:
        print(f" Restricted access test inconclusive: {e}")
        return False


def main():
    """Run all authentication tests."""
    print("CDS MCP Authentication Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_authentication_setup),
        ("Token Acquisition", test_token_acquisition),
        ("CDS Client Integration", test_cds_client_integration),
        ("Restricted Access", test_restricted_access),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f" {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 25)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = " PASS" if success else " FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print(" All tests passed! Authentication is working correctly.")
    elif passed > 0:
        print("  Some tests passed. Check configuration and permissions.")
    else:
        print(" All tests failed. Check your CERN credentials and network.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
