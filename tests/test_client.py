"""
Tests for the FleeksClient.
"""

import pytest
import requests_mock
from fleeks_sdk import FleeksClient
from fleeks_sdk.exceptions import FleeksAPIError, FleeksException


class TestFleeksClient:
    """Test suite for FleeksClient."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.api_key = "test-api-key"
        self.base_url = "https://api.fleeks.com"
        self.client = FleeksClient(api_key=self.api_key, base_url=self.base_url)
    
    def test_client_initialization(self):
        """Test client initialization."""
        assert self.client.api_key == self.api_key
        assert self.client.base_url == self.base_url
        assert "Bearer test-api-key" in self.client.session.headers["Authorization"]
    
    @requests_mock.Mocker()
    def test_health_check_success(self, m):
        """Test successful health check."""
        m.get(f"{self.base_url}/health", json={"status": "ok"})
        
        response = self.client.health_check()
        assert response == {"status": "ok"}
    
    @requests_mock.Mocker()
    def test_get_request(self, m):
        """Test GET request."""
        test_data = {"data": "test"}
        m.get(f"{self.base_url}/test", json=test_data)
        
        response = self.client.get("/test")
        assert response == test_data
    
    @requests_mock.Mocker()
    def test_post_request(self, m):
        """Test POST request."""
        test_data = {"result": "created"}
        m.post(f"{self.base_url}/test", json=test_data)
        
        response = self.client.post("/test", data={"name": "test"})
        assert response == test_data
    
    @requests_mock.Mocker()
    def test_api_error(self, m):
        """Test API error handling."""
        m.get(f"{self.base_url}/error", status_code=400)
        
        with pytest.raises(FleeksAPIError):
            self.client.get("/error")
    
    @requests_mock.Mocker()
    def test_connection_error(self, m):
        """Test connection error handling."""
        m.get(f"{self.base_url}/timeout", exc=requests.exceptions.ConnectTimeout)
        
        with pytest.raises(FleeksException):
            self.client.get("/timeout")