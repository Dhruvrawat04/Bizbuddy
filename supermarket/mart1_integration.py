"""
Mart1 Integration Service
Fetches real-time data from the mart1 billing system API
"""
import requests
import pandas as pd
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class Mart1Integration:
    """Service to connect supermarket analytics with mart1 billing system"""
    
    def __init__(self, base_url: str = None):
        if base_url is None:
            base_url = os.environ.get('MART1_API_URL', 'http://127.0.0.1:8000')
        """
        Initialize the integration service
        
        Args:
            base_url: Base URL of the mart1 API server
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = 10  # seconds
        
    def is_available(self) -> bool:
        """Check if mart1 API is available"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Mart1 API not available: {e}")
            return False
    
    def get_sales_data(self, limit: int = 1000, days: Optional[int] = None) -> Optional[pd.DataFrame]:
        """
        Fetch sales data from mart1
        
        Args:
            limit: Maximum number of records to fetch
            days: Only fetch sales from last N days (optional)
            
        Returns:
            DataFrame with sales data or None if fetch fails
        """
        try:
            params = {"limit": limit}
            if days:
                params["days"] = days
                
            response = requests.get(
                f"{self.base_url}/api/export/sales",
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                df = pd.DataFrame(data["data"])
                logger.info(f"Fetched {len(df)} sales records from mart1")
                return df
            else:
                logger.warning("No sales data returned from mart1")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching sales data from mart1: {e}")
            return None
    
    def get_products_data(self) -> Optional[pd.DataFrame]:
        """
        Fetch product inventory data from mart1
        
        Returns:
            DataFrame with product data or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/export/products",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                df = pd.DataFrame(data["data"])
                logger.info(f"Fetched {len(df)} products from mart1")
                return df
            else:
                logger.warning("No product data returned from mart1")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching products from mart1: {e}")
            return None
    
    def get_category_performance(self, days: int = 30) -> Optional[pd.DataFrame]:
        """
        Fetch category-wise sales performance from mart1
        
        Args:
            days: Number of days to analyze
            
        Returns:
            DataFrame with category performance data or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/export/categories-performance",
                params={"days": days},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                df = pd.DataFrame(data["data"])
                logger.info(f"Fetched category performance data from mart1")
                return df
            else:
                logger.warning("No category performance data returned from mart1")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching category performance from mart1: {e}")
            return None
    
    def get_inventory_status(self) -> Optional[pd.DataFrame]:
        """
        Fetch current inventory status from mart1
        
        Returns:
            DataFrame with inventory status or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/export/inventory-status",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get("data"):
                df = pd.DataFrame(data["data"])
                logger.info(f"Fetched inventory status from mart1")
                return df
            else:
                logger.warning("No inventory data returned from mart1")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching inventory status from mart1: {e}")
            return None
    
    def get_dashboard_summary(self) -> Optional[Dict[str, Any]]:
        """
        Fetch dashboard summary statistics from mart1
        
        Returns:
            Dictionary with summary statistics or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/reports/all-time-analysis",
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info("Fetched dashboard summary from mart1")
            return data
                
        except Exception as e:
            logger.error(f"Error fetching dashboard summary from mart1: {e}")
            return None


# Global instance
_mart1_integration = None

def get_mart1_integration(base_url: str = None) -> Mart1Integration:
    global _mart1_integration
    if _mart1_integration is None:
        if base_url is None:
            base_url = os.environ.get('MART1_API_URL', 'http://127.0.0.1:8000')
        _mart1_integration = Mart1Integration(base_url)
    return _mart1_integration
