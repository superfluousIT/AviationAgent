"""
Test script to validate Aviation Agent components

This script tests the basic functionality without requiring actual API credentials.
"""

import os
import sys

# Mock environment variables for testing
os.environ['AVIATIONSTACK_API_KEY'] = 'test_key'
os.environ['AVIATIONSTACK_BASE_URL'] = 'http://api.aviationstack.com/v1'

def test_aviation_client():
    """Test AviationStackClient initialization and structure."""
    print("Testing AviationStackClient...")
    
    try:
        from aviation_client import AviationStackClient
        
        # Test initialization
        client = AviationStackClient()
        print("  ✓ Client initialization successful")
        
        # Test attributes
        assert hasattr(client, 'api_key'), "Missing api_key attribute"
        assert hasattr(client, 'base_url'), "Missing base_url attribute"
        assert hasattr(client, 'get_flights'), "Missing get_flights method"
        assert hasattr(client, 'search_flights'), "Missing search_flights method"
        print("  ✓ Client has required attributes and methods")
        
        # Test parameter building
        params = {}
        if hasattr(client, 'get_flights'):
            import inspect
            sig = inspect.signature(client.get_flights)
            print(f"  ✓ get_flights accepts {len(sig.parameters)} parameters")
        
        print("✅ AviationStackClient tests passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def test_aviation_agent_structure():
    """Test AviationAgent class structure (without Azure credentials)."""
    print("Testing AviationAgent structure...")
    
    try:
        from aviation_agent import AviationAgent
        
        # Check class attributes
        print("  ✓ AviationAgent class imported successfully")
        
        # Check for required methods
        required_methods = ['chat', 'reset_conversation', '_define_tools', '_execute_tool']
        for method in required_methods:
            assert hasattr(AviationAgent, method), f"Missing {method} method"
        print(f"  ✓ AviationAgent has all required methods")
        
        print("✅ AviationAgent structure tests passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def test_flask_app():
    """Test Flask application structure."""
    print("Testing Flask application...")
    
    try:
        from app import app
        
        # Test app configuration
        assert app is not None, "Flask app not initialized"
        print("  ✓ Flask app initialized")
        
        # Test routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        required_routes = ['/', '/api/chat', '/api/reset', '/health']
        
        for route in required_routes:
            assert route in routes, f"Missing route: {route}"
        print(f"  ✓ All required routes present: {len(routes)} total routes")
        
        print("✅ Flask application tests passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def test_file_structure():
    """Test that all required files exist."""
    print("Testing file structure...")
    
    required_files = [
        'app.py',
        'aviation_agent.py',
        'aviation_client.py',
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md',
        'SETUP.md',
        'templates/index.html'
    ]
    
    base_path = os.path.dirname(os.path.abspath(__file__))
    missing_files = []
    
    for file in required_files:
        file_path = os.path.join(base_path, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
    
    if missing_files:
        print(f"  ✗ Missing files: {', '.join(missing_files)}\n")
        return False
    
    print(f"  ✓ All {len(required_files)} required files present")
    print("✅ File structure tests passed\n")
    return True

def test_gitignore():
    """Test that .gitignore properly excludes sensitive files."""
    print("Testing .gitignore configuration...")
    
    try:
        gitignore_path = os.path.join(os.path.dirname(__file__), '.gitignore')
        with open(gitignore_path, 'r') as f:
            content = f.read()
        
        required_patterns = ['.env', '__pycache__', '*.pyc', 'venv/']
        missing_patterns = []
        
        for pattern in required_patterns:
            if pattern not in content:
                missing_patterns.append(pattern)
        
        if missing_patterns:
            print(f"  ✗ Missing patterns: {', '.join(missing_patterns)}\n")
            return False
        
        print(f"  ✓ All critical patterns present in .gitignore")
        print("✅ .gitignore tests passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def test_requirements():
    """Test that requirements.txt has necessary packages."""
    print("Testing requirements.txt...")
    
    try:
        req_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
        with open(req_path, 'r') as f:
            requirements = f.read()
        
        required_packages = ['Flask', 'python-dotenv', 'requests', 'openai', 'azure-identity']
        missing_packages = []
        
        for package in required_packages:
            if package.lower() not in requirements.lower():
                missing_packages.append(package)
        
        if missing_packages:
            print(f"  ✗ Missing packages: {', '.join(missing_packages)}\n")
            return False
        
        print(f"  ✓ All required packages listed in requirements.txt")
        print("✅ Requirements tests passed\n")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Aviation Agent - Component Tests")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(("File Structure", test_file_structure()))
    results.append((".gitignore", test_gitignore()))
    results.append(("Requirements", test_requirements()))
    results.append(("AviationStackClient", test_aviation_client()))
    results.append(("AviationAgent", test_aviation_agent_structure()))
    results.append(("Flask App", test_flask_app()))
    
    # Print summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The application structure is correct.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
