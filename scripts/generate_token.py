#!/usr/bin/env python3
"""
Command-line utility to generate new access tokens with arbitrary expiration dates.
"""

import argparse
import sys
import os
from datetime import datetime, timedelta, timezone

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.auth import get_auth_manager
from app.config import settings


def generate_token(user_id: str, expiration_days: int = None, expiration_hours: int = None):
    """
    Generate an access token for a user.
    
    Args:
        user_id: User identifier
        expiration_days: Days until expiration (optional)
        expiration_hours: Hours until expiration (optional)
    """
    try:
        # Calculate expiration time
        expires_delta = None
        if expiration_days or expiration_hours:
            expires_delta = timedelta(
                days=expiration_days or 0,
                hours=expiration_hours or 0
            )
        
        # Get the configured authentication manager
        auth_manager = get_auth_manager()
        
        # Check if the auth manager supports token creation
        if not hasattr(auth_manager, 'create_access_token'):
            raise Exception("Current authentication manager doesn't support token creation")
        
        # Generate token
        token = auth_manager.create_access_token(user_id, expires_delta)
        
        # Calculate actual expiration time
        if expires_delta:
            actual_expiry = datetime.now(timezone.utc) + expires_delta
            expiry_str = actual_expiry.strftime("%Y-%m-%d %H:%M:%S UTC")
        else:
            default_expiry = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            expiry_str = default_expiry.strftime("%Y-%m-%d %H:%M:%S UTC")
        
        print(f"Access token generated successfully!")
        print(f"User ID: {user_id}")
        print(f"Token: {token}")
        print(f"Expires: {expiry_str}")
        print(f"Token Type: Bearer")
        print(f"Auth Manager: {type(auth_manager).__name__}")
        print("\nUsage:")
        print(f"Authorization: Bearer {token}")
        
    except Exception as e:
        print(f"Error generating token: {str(e)}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Generate access tokens using the configured authentication manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate token with default expiration (60 minutes)
  python scripts/generate_token.py --user-id john_doe
  
  # Generate token valid for 7 days
  python scripts/generate_token.py --user-id john_doe --days 7
  
  # Generate token valid for 12 hours
  python scripts/generate_token.py --user-id john_doe --hours 12
  
  # Generate token valid for 2 days and 6 hours
  python scripts/generate_token.py --user-id john_doe --days 2 --hours 6
        """
    )
    
    parser.add_argument(
        "--user-id", "-u",
        required=True,
        help="User identifier for the token"
    )
    
    parser.add_argument(
        "--days", "-d",
        type=int,
        help="Days until token expiration"
    )
    
    parser.add_argument(
        "--hours", "-hr",
        type=int,
        help="Hours until token expiration"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.days is not None and args.days < 0:
        print("Error: Days cannot be negative", file=sys.stderr)
        sys.exit(1)
    
    if args.hours is not None and args.hours < 0:
        print("Error: Hours cannot be negative", file=sys.stderr)
        sys.exit(1)
    
    if args.days is None and args.hours is None:
        print("Using default expiration time (60 minutes)")
    
    # Generate token
    generate_token(args.user_id, args.days, args.hours)


if __name__ == "__main__":
    main()
