import requests
import json
import sys
import os

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_EMAIL = 'blaziousmwambuwa@gmail.com'
LOGIN_PASSWORD = 'blaze@003'

def get_headers(token):
    return {'Authorization': f'Bearer {token}'}

def login():
    print("Logging in...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json={
            'email': LOGIN_EMAIL,
            'password': LOGIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get('token')
        else:
            print(f"Login failed: {response.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server at {BASE_URL}. Is it running?")
        sys.exit(1)

def list_projects(token):
    print("\nFetching existing projects...")
    headers = get_headers(token)
    response = requests.get(f"{BASE_URL}/api/projects/", headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to list projects: {response.text}")
        return []
        
    data = response.json()
    # Handle if pagination is involved
    if isinstance(data, dict) and 'results' in data:
        projects = data['results']
    elif isinstance(data, list):
        projects = data
    else:
        print("Unexpected response format for projects list.")
        return []
        
    if not projects:
        print("No projects found.")
        return []

    print(f"\nFound {len(projects)} projects:")
    print("-" * 80)
    print(f"{'#':<4} | {'ID':<36} | {'Status':<12} | {'Title'}")
    print("-" * 80)
    for i, p in enumerate(projects):
        print(f"{i+1:<4} | {p.get('id')} | {p.get('status'):<12} | {p.get('title')}")
        
    return projects

def check_contract(token, project_id):
    print(f"\nChecking contract for Project {project_id}...")
    headers = get_headers(token)
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/contract/", headers=headers)
    
    if response.status_code == 200:
        contract = response.json()
        print(f"Contract found: Status = {contract.get('status')}")
        return contract
    elif response.status_code == 404:
        print("No contract found for this project.")
        return None
    else:
        print(f"Error checking contract: {response.text}")
        return None

def test_deposit(token, project_id, phone):
    print(f"\nInitiating M-Pesa deposit for Project {project_id} with phone {phone}...")
    headers = get_headers(token)
    data = {
        'project_id': project_id,
        'phone_number': phone
    }
    
    response = requests.post(f"{BASE_URL}/api/escrow/deposit/", json=data, headers=headers)
    
    print("\n--- API Response ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)

def main():
    token = login()
    projects = list_projects(token)
    
    if not projects:
        print("\nNo projects available to test.")
        sys.exit(0)
        
    while True:
        choice = input("\nEnter the number of the project to test with (or 'q' to quit): ")
        if choice.lower() == 'q':
            sys.exit(0)
            
        try:
            index = int(choice) - 1
            if 0 <= index < len(projects):
                selected_project = projects[index]
                project_id = selected_project.get('id')
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
            
    # Check contract status (optional info for user)
    check_contract(token, project_id)
        
    phone = input("\nEnter M-Pesa phone number (format 2547...): ").strip()
    if not phone:
        print("Phone number is required.")
        sys.exit(1)
        
    test_deposit(token, project_id, phone)

if __name__ == "__main__":
    main()
