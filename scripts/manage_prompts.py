#!/usr/bin/env python3
"""
Prompt Management Script for Sample OpenRouter Backend
This script demonstrates how to add, update, remove, and view prompt templates.
"""

import requests
import json
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

BASE_URL = "http://localhost:8080"


def get_auth_token(user_id: str = "test_user") -> str:
    """Get an authentication token."""
    try:
        response = requests.post(f"{BASE_URL}/auth/token", params={"user_id": user_id}, timeout=10)
        if response.status_code == 200:
            return response.json().get('access_token')
        else:
            print(f"❌ Failed to get token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting token: {str(e)}")
        return None


def add_prompt_template(token: str, prompt_name: str, template: str, description: str = None):
    """Add a new prompt template."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "prompt_name": prompt_name,
        "prompt_template": template,
        "description": description
    }
    
    try:
        response = requests.post(f"{BASE_URL}/prompts/add", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Added prompt '{prompt_name}': {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to add prompt: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error adding prompt: {str(e)}")
        return False


def update_prompt_template(token: str, prompt_name: str, new_template: str, new_description: str = None):
    """Update an existing prompt template."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "prompt_name": prompt_name,
        "new_template": new_template,
        "new_description": new_description
    }
    
    try:
        response = requests.put(f"{BASE_URL}/prompts/update", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Updated prompt '{prompt_name}': {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to update prompt: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error updating prompt: {str(e)}")
        return False


def remove_prompt_template(token: str, prompt_name: str):
    """Remove a prompt template."""
    headers = {"Authorization": f"Bearer {token}"}
    data = {"prompt_name": prompt_name}
    
    try:
        response = requests.delete(f"{BASE_URL}/prompts/remove", headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Removed prompt '{prompt_name}': {result.get('message')}")
            return True
        else:
            print(f"❌ Failed to remove prompt: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error removing prompt: {str(e)}")
        return False


def get_prompt_info(token: str, prompt_name: str):
    """Get detailed information about a prompt template."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/prompts/{prompt_name}/info", headers=headers, timeout=10)
        if response.status_code == 200:
            info = response.json()
            print(f"\n📋 Prompt Info for '{prompt_name}':")
            print(f"   Variables: {info.get('variables', [])}")
            print(f"   Variable Count: {info.get('variable_count', 0)}")
            print(f"   Built-in: {info.get('is_built_in', False)}")
            print(f"   Description: {info.get('description', 'No description')}")
            print(f"   Template: {info.get('template', '')[:100]}...")
            return True
        else:
            print(f"❌ Failed to get prompt info: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error getting prompt info: {str(e)}")
        return False


def list_all_prompts(token: str):
    """List all available prompts."""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/prompts", headers=headers, timeout=10)
        if response.status_code == 200:
            prompts = response.json().get('prompts', {})
            print(f"\n📝 Available Prompts ({len(prompts)}):")
            for name, description in prompts.items():
                print(f"   • {name}: {description}")
            return True
        else:
            print(f"❌ Failed to list prompts: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error listing prompts: {str(e)}")
        return False


def demo_prompt_management():
    """Demonstrate prompt management functionality."""
    print("🚀 Prompt Management Demo")
    print("=" * 50)
    
    # Get authentication token
    token = get_auth_token()
    if not token:
        print("❌ Cannot proceed without authentication token")
        return
    
    print(f"✅ Authenticated successfully")
    
    # List current prompts
    print("\n📋 Current prompts:")
    list_all_prompts(token)
    
    # Add a new custom prompt
    print("\n➕ Adding new custom prompt...")
    custom_template = """
Please analyze the following {topic} and provide insights:

Topic: {topic}
Context: {context}
Specific Focus: {focus}

Please provide:
1. Key analysis points
2. Recommendations
3. Potential challenges
4. Next steps
"""
    
    add_prompt_template(
        token, 
        "custom_analysis", 
        custom_template, 
        "Custom analysis template for various topics"
    )
    
    # Get info about the new prompt
    print("\n🔍 Getting info about new prompt...")
    get_prompt_info(token, "custom_analysis")
    
    # Update the prompt
    print("\n✏️  Updating the custom prompt...")
    updated_template = """
Please analyze the following {topic} and provide comprehensive insights:

Topic: {topic}
Context: {context}
Specific Focus: {focus}
Additional Requirements: {requirements if requirements else 'None'}

Please provide:
1. Executive Summary
2. Detailed Analysis
3. Key Findings
4. Recommendations
5. Risk Assessment
6. Implementation Plan
"""
    
    update_prompt_template(
        token, 
        "custom_analysis", 
        updated_template, 
        "Enhanced custom analysis template with comprehensive coverage"
    )
    
    # List prompts again to see the changes
    print("\n📋 Updated prompts:")
    list_all_prompts(token)
    
    # Test the new prompt with LLM
    print("\n🤖 Testing the new prompt with LLM...")
    test_data = {
        "prompt_name": "custom_analysis",
        "data": {
            "topic": "Artificial Intelligence in Healthcare",
            "context": "Current state of AI adoption in medical settings",
            "focus": "Patient safety and diagnostic accuracy",
            "requirements": "Focus on practical implementation challenges"
        }
    }
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    try:
        response = requests.post(f"{BASE_URL}/ask-llm", headers=headers, json=test_data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ LLM test successful!")
            print(f"   Model used: {result.get('model_used')}")
            print(f"   Success: {result.get('success')}")
            if result.get('response'):
                print(f"   Response preview: {result.get('response', '')[:200]}...")
        else:
            print(f"❌ LLM test failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error testing LLM: {str(e)}")
    
    # Clean up - remove the custom prompt
    print("\n🧹 Cleaning up - removing custom prompt...")
    remove_prompt_template(token, "custom_analysis")
    
    # Final prompt list
    print("\n📋 Final prompts:")
    list_all_prompts(token)
    
    print("\n🎉 Prompt management demo completed!")


def main():
    """Main function."""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "add" and len(sys.argv) >= 4:
            token = get_auth_token()
            if token:
                add_prompt_template(token, sys.argv[2], sys.argv[3])
            return
        elif command == "update" and len(sys.argv) >= 4:
            token = get_auth_token()
            if token:
                update_prompt_template(token, sys.argv[2], sys.argv[3])
            return
        elif command == "remove" and len(sys.argv) >= 3:
            token = get_auth_token()
            if token:
                remove_prompt_template(token, sys.argv[2])
            return
        elif command == "info" and len(sys.argv) >= 3:
            token = get_auth_token()
            if token:
                get_prompt_info(token, sys.argv[2])
            return
        elif command == "list":
            token = get_auth_token()
            if token:
                list_all_prompts(token)
            return
        elif command == "demo":
            demo_prompt_management()
            return
        else:
            print("❌ Invalid command or missing arguments")
            print_usage()
            return
    
    # Default to demo mode
    demo_prompt_management()


def print_usage():
    """Print usage information."""
    print("\n📖 Usage:")
    print("  python scripts/manage_prompts.py [command] [args...]")
    print("\nCommands:")
    print("  demo                    - Run interactive demo")
    print("  add <name> <template>  - Add new prompt template")
    print("  update <name> <template> - Update existing prompt")
    print("  remove <name>          - Remove prompt template")
    print("  info <name>            - Get prompt information")
    print("  list                   - List all prompts")
    print("\nExamples:")
    print("  python scripts/manage_prompts.py demo")
    print("  python scripts/manage_prompts.py add my_prompt 'Hello {name}!'")
    print("  python scripts/manage_prompts.py info company_analysis")


if __name__ == "__main__":
    main()
