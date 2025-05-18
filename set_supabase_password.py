#!/usr/bin/env python
"""
Simple utility to set the SUPABASE_PASSWORD environment variable.
This avoids storing the password in plaintext files or command history.
"""
import os
import sys
import subprocess
from getpass import getpass

def set_env_var_for_session():
    """Set environment variable for the current Python session."""
    password = getpass("Enter your Supabase database password: ")
    os.environ["SUPABASE_PASSWORD"] = password
    print("SUPABASE_PASSWORD environment variable set for this session.")
    return password

def set_env_var_for_powershell(password=None):
    """Set environment variable for PowerShell."""
    if password is None:
        password = getpass("Enter your Supabase database password: ")
    
    # Create a PowerShell command to set the environment variable
    ps_command = f'$env:SUPABASE_PASSWORD = "{password}"'
    
    # Print command for user to copy-paste
    print("\nRun this command in your PowerShell terminal:")
    print(f'$env:SUPABASE_PASSWORD = "YOUR_PASSWORD_HERE"')
    print("\nReplace YOUR_PASSWORD_HERE with your actual password.")
    print("This will set the variable for your current PowerShell session only.")
    
    return password

if __name__ == "__main__":
    # Set for Python session
    password = set_env_var_for_session()
    
    # Provide instructions for PowerShell
    set_env_var_for_powershell(password)
    
    print("\nTo use Supabase connection now, run your application in the same terminal session.")
    print("For example: uvicorn app.main:app --reload") 