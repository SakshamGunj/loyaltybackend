import requests
import json
import time
import sys

# Base URL of your API
BASE_URL = "http://localhost:8090/api/ordering"

# Sample JWT token (this is a dummy token, replace with a real one)
ADMIN_JWT = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbjEyMyIsIm5hbWUiOiJBZG1pbiBVc2VyIiwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSIsInJvbGUiOiJhZG1pbiIsImlhdCI6MTUxNjIzOTAyMn0.3FKqnFqvPHQBgQusL_GBrw3hG9Vz8JhY2SR0c_FJmUk"


def load_json_data(file_path):
    """Load JSON data from a file"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {file_path} file not found!")
        return None
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {file_path}!")
        return None


def add_categories(restaurant_id, categories):
    """Add food categories to the restaurant menu"""
    
    print(f"\n=== Adding {len(categories)} Categories to Restaurant ID: {restaurant_id} ===")
    
    added_categories = []
    
    for idx, category in enumerate(categories, 1):
        try:
            # API endpoint for adding a category
            url = f"{BASE_URL}/menu/categories?restaurant_id={restaurant_id}"
            
            # Set the Authorization header with the JWT token
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ADMIN_JWT}"
            }
            
            # Make the POST request
            response = requests.post(url, headers=headers, json=category)
            
            # Check if the request was successful
            if response.status_code == 200 or response.status_code == 201:
                category_response = response.json()
                print(f"✓ Added category {idx}/{len(categories)}: {category['name']}")
                added_categories.append(category_response)
            else:
                print(f"✗ Failed to add category {category['name']}. Status code: {response.status_code}")
                print("Response:", response.text)
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error while adding category {category['name']}. Make sure the API server is running.")
        except Exception as e:
            print(f"✗ Error adding category {category['name']}: {str(e)}")
    
    print(f"\n✓ Successfully added {len(added_categories)}/{len(categories)} categories")
    return added_categories


def add_menu_items(restaurant_id, menu_items, categories):
    """Add menu items to the restaurant"""
    
    print(f"\n=== Adding {len(menu_items)} Menu Items to Restaurant ID: {restaurant_id} ===")
    
    # Create a mapping from category_id in the JSON to actual category_id from API
    category_map = {}
    for i, category in enumerate(categories, 1):
        category_map[i] = category.get('id')
    
    added_items = []
    
    for idx, item in enumerate(menu_items, 1):
        try:
            # Map the category_id from our JSON to the actual category_id
            api_category_id = category_map.get(item['category_id'])
            if not api_category_id:
                print(f"✗ Skipping item {item['name']}: Category ID {item['category_id']} not found in added categories")
                continue
                
            # Create the payload
            payload = {
                "restaurant_id": restaurant_id,
                "name": item['name'],
                "description": item['description'],
                "price": item['price'],
                "available": item['available'],
                "category_id": api_category_id
            }
            
            # API endpoint for adding a menu item
            url = f"{BASE_URL}/menu/items?restaurant_id={restaurant_id}"
            
            # Set the Authorization header with the JWT token
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {ADMIN_JWT}"
            }
            
            # Make the POST request
            response = requests.post(url, headers=headers, json=payload)
            
            # Check if the request was successful
            if response.status_code == 200 or response.status_code == 201:
                item_response = response.json()
                print(f"✓ Added item {idx}/{len(menu_items)}: {item['name']} (${item['price']})")
                added_items.append(item_response)
            else:
                print(f"✗ Failed to add item {item['name']}. Status code: {response.status_code}")
                print("Response:", response.text)
                
        except requests.exceptions.ConnectionError:
            print(f"✗ Connection error while adding item {item['name']}. Make sure the API server is running.")
        except Exception as e:
            print(f"✗ Error adding item {item['name']}: {str(e)}")
    
    print(f"\n✓ Successfully added {len(added_items)}/{len(menu_items)} menu items")
    return added_items


def fetch_menu(restaurant_id):
    """Fetch the complete menu for a restaurant"""
    
    print(f"\n=== Fetching Menu for Restaurant ID: {restaurant_id} ===")
    
    try:
        # API endpoint for getting the menu
        url = f"{BASE_URL}/menu?restaurant_id={restaurant_id}"
        
        # Make the GET request
        response = requests.get(url)
        
        # Check if the request was successful
        if response.status_code == 200:
            menu = response.json()
            
            print("\n=== Menu Summary ===")
            
            # Group items by category
            items_by_category = {}
            for item in menu:
                category_name = item.get('category', {}).get('name', 'Uncategorized')
                if category_name not in items_by_category:
                    items_by_category[category_name] = []
                items_by_category[category_name].append(item)
            
            # Print menu by category
            for category, items in items_by_category.items():
                print(f"\n== {category} ==")
                for item in items:
                    status = "✓" if item.get('available') else "✗"
                    print(f"{status} {item.get('name')} - ₹{item.get('price'):.2f}")
                    print(f"   {item.get('description')}")
            
            return menu
        else:
            print(f"\n✗ Failed to fetch menu. Status code: {response.status_code}")
            print("Response:", response.text)
            return None
            
    except requests.exceptions.ConnectionError:
        print("\n✗ Connection error. Make sure the API server is running.")
        return None
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        return None


def demo_menu_setup(restaurant_id=None):
    """Run a full demo of setting up a restaurant menu"""
    
    if not restaurant_id:
        # Try to get restaurant_id from command line
        if len(sys.argv) > 1:
            restaurant_id = sys.argv[1]
        else:
            restaurant_id = input("Please enter the restaurant ID: ").strip()
    
    print("\n" + "="*50)
    print("RESTAURANT MENU SETUP DEMO")
    print("="*50)
    print(f"Setting up menu for Restaurant ID: {restaurant_id}")
    
    # Load the menu data
    menu_data = load_json_data('menu_items_demo.json')
    if not menu_data:
        print("\nDemo failed: Could not load menu data.")
        return
    
    # Step 1: Add categories
    print("\nStep 1: Adding menu categories...")
    categories = add_categories(restaurant_id, menu_data['categories'])
    if not categories:
        print("\nDemo failed: Could not add categories.")
        return
    
    time.sleep(1)  # Small delay for readability
    
    # Step 2: Add menu items
    print("\nStep 2: Adding menu items...")
    menu_items = add_menu_items(restaurant_id, menu_data['menu_items'], categories)
    if not menu_items:
        print("\nDemo failed: Could not add menu items.")
        return
    
    time.sleep(1)  # Small delay for readability
    
    # Step 3: Fetch and display the complete menu
    print("\nStep 3: Fetching the complete menu...")
    menu = fetch_menu(restaurant_id)
    if not menu:
        print("\nDemo warning: Could not fetch menu.")
    
    # Demo complete
    print("\n" + "="*50)
    print("MENU SETUP DEMO COMPLETED SUCCESSFULLY!")
    print("="*50)
    print("\nYou have successfully:")
    print(f"✓ Added {len(categories)} menu categories")
    print(f"✓ Added {len(menu_items)} menu items")
    print("✓ Displayed the complete restaurant menu")
    
    print("\nNext steps could include:")
    print("• Place test orders using this menu")
    print("• Update menu items (e.g., change prices or availability)")
    print("• Add more categories and items")
    

if __name__ == "__main__":
    # Check if restaurant_id was provided as a command-line argument
    restaurant_id = None
    if len(sys.argv) > 1:
        restaurant_id = sys.argv[1]
        
    demo_menu_setup(restaurant_id) 