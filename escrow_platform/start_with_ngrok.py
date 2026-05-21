import os
import sys
import subprocess
from pyngrok import ngrok
from dotenv import load_dotenv

def update_env(url):
    env_path = '.env'
    try:
        with open(env_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    
    new_lines = []
    found = False
    callback_url = f"{url}/api/mpesa/callback/deposit"
    
    for line in lines:
        if line.startswith('MPESA_CALLBACK_URL='):
            new_lines.append(f'MPESA_CALLBACK_URL={callback_url}\n')
            found = True
        else:
            new_lines.append(line)
            
    if not found:
        new_lines.append(f'\nMPESA_CALLBACK_URL={callback_url}\n')
        
    with open(env_path, 'w') as f:
        f.writelines(new_lines)

def main():
    # Kill any existing ngrok processes (optional, but good for cleanup)
    # subprocess.call(['taskkill', '/F', '/IM', 'ngrok.exe'], stderr=subprocess.DEVNULL)

    print(" * Starting Ngrok tunnel on port 8000...")
    
    # Authenticate Ngrok
    load_dotenv()
    auth_token = os.getenv('NGROK_AUTHTOKEN')
    if auth_token:
        ngrok.set_auth_token(auth_token)
    else:
        print(" * WARNING: No NGROK_AUTHTOKEN found in .env. Ngrok may fail if not already authenticated.")

    try:
        # Connect to ngrok
        url = ngrok.connect(8000).public_url
        print(f" * Ngrok Tunnel Established: {url}")
        
        # Update .env
        update_env(url)
        print(" * Updated .env with new MPESA_CALLBACK_URL")
        print(f" * Access Admin Board at: {url}/admin")
        
        # Run Django Server
        print(" * Starting Django Server...")
        subprocess.call([sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'])
        
    except KeyboardInterrupt:
        print("\n * Shutting down...")
        ngrok.kill()
        sys.exit(0)
    except Exception as e:
        print(f" * Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
