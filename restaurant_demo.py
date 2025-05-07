import requests
import json
import time
from pprint import pprint

# Base URL of your API
BASE_URL = "http://localhost:8090/api/ordering"

# Sample JWT token (this is a dummy token, replace with a real one)
ADMIN_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsIm5hbWUiOiJBZG1pbiBVc2VyIiwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0.3FKqnFqvPHQBgQusL_GBrw3hG9Vz8JhY2SR0c_FJmUk"
USER_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyNDU2IiwibmFtZSI6IlRlc3QgVXNlciIsImVtYWlsIjoidXNlckBleGFtcGxlLmNvbSIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNTE2MjM5MDIyfQ.1fvyrG1V9zoOUEjUdwnV033sde1X8nnW7FmOr8_nfpA"

def register_restaurant():
    """Register a new restaurant with the demo data"""
    
    # Load the restaurant data from the JSON file
    try:
        with open('restaurant_demo_data.json', 'r') as f:
            restaurant_data = json.load(f)
    except FileNotFoundError:
        print("Error: restaurant_demo_data.json file not found!")
        return
    
    print("\n=== Registering New Restaurant ===")
    print(f"Name: {restaurant_data['restaurant_name']}")
    print(f"Points per Rupee: {restaurant_data['points_per_rupee']}")
    print(f"Points per Spin: {restaurant_data['points_per_spin']}")
    print(f"Number of Offers: {len(restaurant_data['offers'])}")
    print("Trying to register...")
    
    try:
        # API endpoint for registering a restaurant
        url = f"{BASE_URL}/restaurants/register-restaurant"
        
        # Set the Authorization header with the JWT token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ADMIN_JWT}"
        }
        
        # Make the POST request
        response = requests.post(url, headers=headers, json=restaurant_data)
        
        # Check if the request was successful
        if response.status_code == 200 or response.status_code == 201:
            print("\n✓ Restaurant registered successfully!")
            restaurant_response = response.json()
            print("\n=== Restaurant Details ===")
            print(f"ID: {restaurant_response.get('restaurant_id')}")
            print(f"Name: {restaurant_response.get('restaurant_name')}")
            print(f"Created at: {restaurant_response.get('created_at')}")
            return restaurant_response
        else:
            print(f"\n✗ Failed to register restaurant. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection error. Make sure the API server is running.")
        return None
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None

def get_restaurant(restaurant_id):
    """Get details for a specific restaurant"""
    
    print(f"\n=== Getting Details for Restaurant ID: {restaurant_id} ===")
    
    try:
        # API endpoint for getting a restaurant
        url = f"{BASE_URL}/restaurants/{restaurant_id}"
        
        # Make the GET request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            restaurant = response.json()
            print("\n✓ Restaurant details retrieved successfully!")
            print("\n=== Restaurant Summary ===")
            print(f"Name: {restaurant.get('restaurant_name')}")
            print(f"Offers: {', '.join(restaurant.get('offers', []))}")
            print(f"Points per Rupee: {restaurant.get('points_per_rupee')}")
            
            print("\n=== Reward Thresholds ===")
            for threshold in restaurant.get('reward_thresholds', []):
                print(f"• {threshold.get('name')}: {threshold.get('points')} points - {threshold.get('reward')}")
                
            return restaurant
        else:
            print(f"\n✗ Failed to get restaurant. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection error. Make sure the API server is running.")
        return None
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None

def create_loyalty_record(restaurant_id):
    """Create a loyalty record for a user"""
    
    print(f"\n=== Creating Loyalty Record for Restaurant ID: {restaurant_id} ===")
    
    # Sample loyalty data
    loyalty_data = {
        "uid": "user456",
        "restaurant_id": restaurant_id,
        "total_points": 0,
        "restaurant_points": 0,
        "tier": "Bronze",
        "punches": 0,
        "redemption_history": [],
        "visited_restaurants": [restaurant_id],
        "last_spin_time": None,
        "spin_history": [],
        "referral_codes": {},
        "referrals_made": [],
        "referred_by": {}
    }
    
    try:
        # API endpoint for creating loyalty
        url = f"{BASE_URL}/loyalty"
        
        # Set the Authorization header with the JWT token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {USER_JWT}"
        }
        
        # Make the POST request
        response = requests.post(url, headers=headers, json=loyalty_data)
        
        # Check if the request was successful
        if response.status_code == 200 or response.status_code == 201:
            print("\n✓ Loyalty record created successfully!")
            loyalty_response = response.json()
            print("\n=== Loyalty Details ===")
            print(f"User ID: {loyalty_response.get('uid')}")
            print(f"Restaurant ID: {loyalty_response.get('restaurant_id')}")
            print(f"Tier: {loyalty_response.get('tier')}")
            print(f"Points: {loyalty_response.get('restaurant_points')}")
            return loyalty_response
        else:
            print(f"\n✗ Failed to create loyalty record. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection error. Make sure the API server is running.")
        return None
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None

def demo_restaurant_registration():
    """Run a full demo of restaurant registration and related operations"""
    
    print("\n" + "="*50)
    print("RESTAURANT REGISTRATION & LOYALTY DEMO")
    print("="*50)
    
    # Step 1: Register a restaurant
    restaurant = register_restaurant()
    if not restaurant:
        print("\nDemo failed at restaurant registration step.")
        return
    
    restaurant_id = restaurant.get('restaurant_id')
    time.sleep(1)  # Small delay for readability
    
    # Step 2: Get the restaurant details
    restaurant_details = get_restaurant(restaurant_id)
    if not restaurant_details:
        print("\nDemo failed at getting restaurant details step.")
        return
    
    time.sleep(1)  # Small delay for readability
    
    # Step 3: Create a loyalty record for a user
    loyalty = create_loyalty_record(restaurant_id)
    if not loyalty:
        print("\nDemo failed at creating loyalty record step.")
        return
    
    # Demo complete
    print("\n" + "="*50)
    print("DEMO COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nYou have successfully:")
    print("✓ Registered a new restaurant")
    print("✓ Retrieved restaurant details")
    print("✓ Created a loyalty record for a user")
    print("\nNext steps could include:")
    print("• Adding menu items and categories")
    print("• Creating an order")
    print("• Claiming rewards")
    print("• Testing the referral system")
    
if __name__ == "__main__":
    demo_restaurant_registration() 