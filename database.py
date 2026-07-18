import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any

# Assuming the region is configured via environment variables or default AWS config
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME", "spotify_users")

def get_dynamodb_resource():
    # If testing locally, you might configure endpoint_url here,
    # but for AWS it uses the default credentials chain.
    return boto3.resource("dynamodb")

def get_user(user_id: str) -> Optional[Dict[str, Any]]:
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    
    try:
        response = table.get_item(Key={"user_id": user_id})
        return response.get("Item")
    except ClientError as e:
        print(f"Error getting user {user_id}: {e}")
        return None

def upsert_user(user_id: str, access_token: str, refresh_token: Optional[str], expires_at: int) -> None:
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    
    # We use put_item which overwrites the item if it exists
    item = {
        "user_id": user_id,
        "access_token": access_token,
        "expires_at": expires_at
    }
    if refresh_token:
        item["refresh_token"] = refresh_token
        
    try:
        table.put_item(Item=item)
    except ClientError as e:
        print(f"Error upserting user {user_id}: {e}")

def delete_user(user_id: str) -> None:
    dynamodb = get_dynamodb_resource()
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)
    
    try:
        table.delete_item(Key={"user_id": user_id})
    except ClientError as e:
        print(f"Error deleting user {user_id}: {e}")
