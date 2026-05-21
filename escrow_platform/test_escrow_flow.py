import requests
import json
import uuid

# Configuration
BASE_URL = 'http://127.0.0.1:8000'
LOGIN_EMAIL = 'blaziousmwambuwa@gmail.com'
LOGIN_PASSWORD = 'blaze@003'  # User provided password

def print_response(response, label):
    print(f"\n--- {label} ---")
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
    return response

def main():
    session = requests.Session()

    # 1. Login
    print("1. Logging in...")
    auth_data = {
        'email': LOGIN_EMAIL,
        'password': LOGIN_PASSWORD
    }
    
    # Try admin login or regular login endpoint depending on implementation
    # Based on urls.py checking '/api/auth/login/'
    response = session.post(f"{BASE_URL}/api/auth/login/", json=auth_data)
    if response.status_code != 200:
        print("Login failed! Please check credentials in the script.")
        return

    token = response.json().get('token')
    headers = {'Authorization': f'Bearer {token}'}
    print("Login successful.")

    # 2. Create Project
    print("\n2. Creating Test Project...")
    project_data = {
        'title': 'Test Escrow Project',
        'description': 'A test project to verify M-Pesa integration',
        'scope_of_work': 'Complete testing',
        'timeline': '2026-12-31',
        'budget': 10.00  # Small amount for testing
    }
    response = requests.post(f"{BASE_URL}/api/projects/", json=project_data, headers=headers)
    print_response(response, "Create Project")
    
    if response.status_code != 201:
        return
        
    project_id = response.json()['id']

    # 3. View Contract (Auto-generated)
    print("\n3. Fetching Contract...")
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/contract/", headers=headers)
    print_response(response, "Get Contract")
    if response.status_code != 200:
        return
    contract_id = response.json().get('id')

    # 4. Initiate Deposit
    print("\n4. Initiating M-Pesa Deposit...")
    deposit_data = {
        'contract_id': contract_id
    }
    
    response = requests.post(f"{BASE_URL}/api/escrow/deposit/", json=deposit_data, headers=headers)
    print_response(response, "Escrow Deposit")
    
    if response.status_code == 200:
        print("\nSUCCESS: Check your phone for the STK Push.")
        print("Once paid, the callback should hit your Ngrok URL.")

if __name__ == '__main__':
    main()
