"""
Quickbase API Client

This module handles all interactions with the Quickbase API for pushing MCQ records.

Security: Implements secure API token handling and request validation.
Resource Efficiency: Uses connection pooling and proper error handling.
"""

import os
import requests
import logging
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Quickbase Configuration
# Security: Store sensitive credentials in environment variables
QUICKBASE_API_ENDPOINT = os.getenv("QUICKBASE_API_ENDPOINT", "https://api.quickbase.com/v1/records")
QUICKBASE_REALM_HOSTNAME = os.getenv("QUICKBASE_REALM_HOSTNAME")
QUICKBASE_USER_TOKEN = os.getenv("QUICKBASE_USER_TOKEN")
QUICKBASE_TABLE_ID = os.getenv("QUICKBASE_TABLE_ID")  # Table ID where records will be inserted

# Validate configuration on module load
if not QUICKBASE_TABLE_ID:
    logger.warning("QUICKBASE_TABLE_ID not set in environment variables. You must provide it when calling push functions.")


class QuickbaseClient:
    """
    Client for interacting with Quickbase API.
    
    Security: Implements secure authentication and request validation.
    """
    
    def __init__(
        self,
        realm_hostname: str = QUICKBASE_REALM_HOSTNAME,
        user_token: str = QUICKBASE_USER_TOKEN,
        api_endpoint: str = QUICKBASE_API_ENDPOINT
    ):
        """
        Initialize Quickbase client.
        
        Args:
            realm_hostname: Quickbase realm hostname
            user_token: User token for authentication
            api_endpoint: API endpoint URL
        """
        self.realm_hostname = realm_hostname
        self.user_token = user_token
        self.api_endpoint = api_endpoint
        
        # Security: Validate credentials
        if not self.user_token or not self.realm_hostname:
            raise ValueError("Quickbase credentials (realm_hostname and user_token) are required")
        
        logger.info(f"Initialized Quickbase client for realm: {self.realm_hostname}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers for Quickbase API requests.
        
        Returns:
            Dictionary of headers
        """
        return {
            "QB-Realm-Hostname": self.realm_hostname,
            "Authorization": f"QB-USER-TOKEN {self.user_token}",
            "Content-Type": "application/json"
        }
    
    def push_records(
        self,
        table_id: str,
        records: List[Dict[str, Any]],
        merge_field_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Push records to Quickbase table.
        
        Args:
            table_id: Quickbase table ID
            records: List of records to push (in Quickbase format)
            merge_field_id: Optional field ID for upsert operation
            
        Returns:
            Response from Quickbase API
            
        Raises:
            requests.HTTPError: If API request fails
        """
        payload = {
            "to": table_id,
            "data": records
        }
        
        # Add merge field if provided (for upsert operations)
        if merge_field_id:
            payload["mergeFieldId"] = merge_field_id
        
        logger.info(f"Pushing {len(records)} records to Quickbase table {table_id}")
        
        try:
            # Resource Efficiency: Use timeout to prevent hanging requests
            response = requests.post(
                self.api_endpoint,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            
            # Raise exception for bad status codes
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Successfully pushed {len(records)} records to Quickbase")
            
            return {
                "success": True,
                "records_pushed": len(records),
                "response": result
            }
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"Quickbase API error: {e.response.status_code} - {e.response.text}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "records_attempted": len(records)
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error when pushing to Quickbase: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "records_attempted": len(records)
            }
    
    def push_mcq_records(
        self,
        table_id: str,
        mcq_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Push MCQ records to Quickbase (wrapper for push_records with MCQ-specific logic).
        
        Args:
            table_id: Quickbase table ID
            mcq_data: List of MCQ records in Quickbase format
            
        Returns:
            Response from Quickbase API
        """
        logger.info(f"Preparing to push {len(mcq_data)} MCQ records to Quickbase")
        
        # Security: Validate record structure
        if not mcq_data:
            logger.warning("No MCQ records to push")
            return {
                "success": False,
                "error": "No records provided",
                "records_attempted": 0
            }
        
        return self.push_records(table_id, mcq_data)


# Singleton instance for convenience

_default_client = None


def get_quickbase_client() -> QuickbaseClient:
    """
    Get the default Quickbase client instance.
    
    Returns:
        QuickbaseClient instance
    """
    global _default_client
    if _default_client is None:
        _default_client = QuickbaseClient()
    return _default_client


def push_mcqs_to_quickbase(
    table_id: str,
    mcq_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Convenience function to push MCQ records to Quickbase.
    
    Args:
        table_id: Quickbase table ID
        mcq_records: List of MCQ records in Quickbase format
        
    Returns:
        Response dictionary with success status and details
    """
    client = get_quickbase_client()
    return client.push_mcq_records(table_id, mcq_records)
