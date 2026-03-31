"""
Quickbase Integration Test Script

This script simulates how Quickbase will call the MCQ Generator API.
Use this to test your deployment before connecting Quickbase.
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = input("Enter your API URL (e.g., http://localhost:8000): ").strip()
API_KEY = os.getenv("API_KEY")  # Optional - only if authentication is enabled

# Test categories
CATEGORIES = ['agriculture', 'climate', 'renewable_energy']


def test_health_check():
    """Test the health endpoint (no authentication needed)."""
    print("\n" + "="*70)
    print("Testing Health Check Endpoint")
    print("="*70)
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        
        print("✅ Health check successful!")
        print(json.dumps(data, indent=2))
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_generate_mcqs(category):
    """
    Test MCQ generation endpoint (simulates Quickbase request).
    
    This is exactly what Quickbase will send.
    """
    print("\n" + "="*70)
    print(f"Testing MCQ Generation for Category: {category.upper()}")
    print("="*70)
    
    # Prepare headers (as Quickbase would)
    headers = {
        "Content-Type": "application/json"
    }
    
    # Add API key if configured (Quickbase should include this too)
    if API_KEY:
        headers["X-API-Key"] = API_KEY
        print(f"🔑 Using API Key authentication")
    
    # Prepare payload (exactly as Quickbase sends)
    payload = {
        "category": category
    }
    
    print(f"📤 Sending request to: {API_BASE_URL}/generate-mcqs")
    print(f"📄 Payload: {json.dumps(payload)}")
    
    try:
        # Make request (same as Quickbase Pipeline HTTP Request step)
        response = requests.post(
            f"{API_BASE_URL}/generate-mcqs",
            headers=headers,
            json=payload,
            timeout=120  # Allow time for MCQ generation
        )
        
        # Check HTTP status
        print(f"📊 HTTP Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("✅ MCQ Generation Successful!")
            print(f"   Category: {data['category']}")
            print(f"   Status: {data['status']}")
            print(f"   Total Sets: {data['total_sets']}")
            print(f"   Message: {data.get('message', 'N/A')}")
            
            # Display summary of generated MCQs
            print("\n   Generated MCQ Sets:")
            for mcq_set in data['mcq_sets']:
                print(f"   - Set {mcq_set['set_number']}: {mcq_set['total_questions']} questions")
            
            # Display first question as example
            if data['mcq_sets'] and data['mcq_sets'][0]['questions']:
                print("\n   📝 Sample Question (Set 1, Question 1):")
                q = data['mcq_sets'][0]['questions'][0]
                print(f"   Q: {q['question']}")
                print(f"   A: {q['options']['A']}")
                print(f"   B: {q['options']['B']}")
                print(f"   C: {q['options']['C']}")
                print(f"   D: {q['options']['D']}")
                print(f"   Correct Answer: {q['correct_answer']}")
                print(f"   Explanation: {q['explanation'][:100]}...")
            
            # Save full response to file
            output_file = f"quickbase_test_{category}_response.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\n   💾 Full response saved to: {output_file}")
            
            return True
            
        elif response.status_code == 401:
            print("❌ Authentication failed!")
            print("   - Check X-API-Key header value")
            print("   - Verify API_KEY in .env matches")
            print(f"   Response: {response.text}")
            return False
            
        elif response.status_code == 400:
            print("❌ Bad request!")
            print("   - Check category value is valid")
            print(f"   Response: {response.text}")
            return False
            
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out!")
        print("   - MCQ generation can take 30-120 seconds")
        print("   - Check if API service is running")
        print("   - Increase timeout if needed")
        return False
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection error!")
        print("   - Verify API URL is correct")
        print("   - Check if API service is running")
        print("   - Check network/firewall settings")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_quickbase_scenario():
    """
    Simulate complete Quickbase scenario:
    1. User creates record in Quickbase
    2. Pipeline triggers
    3. API is called
    4. Response is received
    5. Data is parsed and stored
    """
    print("\n" + "="*70)
    print("QUICKBASE INTEGRATION SIMULATION")
    print("="*70)
    print("\nThis simulates the complete Quickbase Pipeline flow:")
    print("1. Quickbase Pipeline triggers")
    print("2. HTTP POST request sent to API")
    print("3. API processes and returns MCQs")
    print("4. Quickbase receives and parses response")
    print("5. Data is stored in Quickbase tables")
    
    # Step 1: Health check
    if not test_health_check():
        print("\n⚠️  API health check failed. Fix issues before testing Quickbase integration.")
        return
    
    # Step 2: Test each category (simulate 3 Quickbase pipeline runs)
    print("\n" + "-"*70)
    print("Simulating Quickbase Pipeline Executions")
    print("-"*70)
    
    results = {}
    for category in CATEGORIES:
        success = test_generate_mcqs(category)
        results[category] = "✅ Success" if success else "❌ Failed"
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for category, status in results.items():
        print(f"{category.ljust(20)}: {status}")
    
    print("\n" + "="*70)
    print("NEXT STEPS FOR QUICKBASE")
    print("="*70)
    
    if all("✅" in status for status in results.values()):
        print("✅ All tests passed! Ready for Quickbase integration.")
        print("\nQuickbase Pipeline Configuration:")
        print(f"1. POST URL: {API_BASE_URL}/generate-mcqs")
        print("2. Headers:")
        print("   - Content-Type: application/json")
        if API_KEY:
            print(f"   - X-API-Key: {API_KEY}")
        print('3. Body: {"category": "{{category_field}}"}')
        print("\nSee QUICKBASE_INTEGRATION.md for detailed setup instructions.")
    else:
        print("⚠️  Some tests failed. Fix issues before Quickbase integration.")
        print("Check API logs and troubleshooting section in documentation.")


if __name__ == "__main__":
    print("="*70)
    print("MCQ GENERATOR API - QUICKBASE INTEGRATION TEST")
    print("="*70)
    print(f"\nAPI URL: {API_BASE_URL}")
    print(f"Authentication: {'Enabled (API Key required)' if API_KEY else 'Disabled'}")
    
    print("\nOptions:")
    print("1. Full Quickbase Simulation (all categories)")
    print("2. Test single category")
    print("3. Health check only")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        test_quickbase_scenario()
    elif choice == "2":
        print("\nCategories:")
        for idx, cat in enumerate(CATEGORIES, 1):
            print(f"{idx}. {cat}")
        cat_choice = input("Select category (1-3): ").strip()
        if cat_choice in ["1", "2", "3"]:
            test_generate_mcqs(CATEGORIES[int(cat_choice) - 1])
    elif choice == "3":
        test_health_check()
    else:
        print("Invalid option")
    
    print("\n" + "="*70)
    print("Test complete!")
    print("="*70)
