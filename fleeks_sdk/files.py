"""
File management - matches backend /api/v1/sdk/files endpoints exactly.

Backend endpoints:
- POST /api/v1/sdk/files/{project_id}
- GET /api/v1/sdk/files/{project_id}
- GET /api/v1/sdk/files/{project_id}/content
- PUT /api/v1/sdk/files/{project_id}/content
- DELETE /api/v1/sdk/files/{project_id}/content
- POST /api/v1/sdk/files/{project_id}/directories
- POST /api/v1/sdk/files/{project_id}/upload
"""

from typing import Dict, Any, List, Optional, BinaryIO, Union
from pathlib import Path
from .models import FileInfo, DirectoryListing
from .exceptions import FleeksResourceNotFoundError, FleeksAPIError, FleeksValidationError


class FileManager:
    """
    Manager for file operations.
    
    Provides comprehensive file system access including:
    - Creating, reading, updating, deleting files
    - Directory management
    - File uploads
    - Recursive directory listing
    """
    
    def __init__(self, client, project_id: str):
        """
        Initialize file manager.
        
        Args:
            client: FleeksClient instance
            project_id: Project/workspace ID
        """
        self.client = client
        self.project_id = project_id
    
    async def create(
        self,
        path: str,
        content: str = "",
        encoding: str = "utf-8",
        permissions: Optional[str] = None
    ) -> FileInfo:
        """
        Create a new file.
        
        POST /api/v1/sdk/files/{project_id}
        
        Args:
            path: File path relative to workspace root
            content: File content
            encoding: Text encoding (default: utf-8)
            permissions: File permissions (e.g., "0644")
        
        Returns:
            FileInfo: Created file information
        
        Example:
            >>> file = await workspace.files.create(
            ...     path="src/main.py",
            ...     content="print('Hello, World!')"
            ... )
            >>> print(f"Created: {file.path}")
        """
        data = {
            'path': path,
            'content': content,
            'encoding': encoding
        }
        if permissions:
            data['permissions'] = permissions
        
        response = await self.client._make_request(
            'POST',
            f'/api/v1/sdk/files/{self.project_id}',
            json=data
        )
        return FileInfo.from_dict(response)
    
    async def list(
        self,
        path: str = "/",
        recursive: bool = False,
        include_hidden: bool = False
    ) -> DirectoryListing:
        """
        List files and directories.
        
        GET /api/v1/sdk/files/{project_id}
        
        Args:
            path: Directory path (default: root "/")
            recursive: Include subdirectories recursively
            include_hidden: Include hidden files (starting with .)
        
        Returns:
            DirectoryListing: Files and directories with metadata
        
        Example:
            >>> listing = await workspace.files.list(path="/src", recursive=True)
            >>> print(f"Found {listing.total_count} items")
            >>> for file in listing.get_files():
            ...     print(f"  {file.path} ({file.size_bytes} bytes)")
        """
        params = {
            'path': path,
            'recursive': recursive,
            'include_hidden': include_hidden
        }
        
        response = await self.client._make_request(
            'GET',
            f'/api/v1/sdk/files/{self.project_id}',
            params=params
        )
        return DirectoryListing.from_dict(response)
    
    async def read(
        self,
        path: str,
        encoding: str = "utf-8"
    ) -> str:
        """
        Read file content.
        
        GET /api/v1/sdk/files/{project_id}/content
        
        Args:
            path: File path relative to workspace root
            encoding: Text encoding (default: utf-8)
        
        Returns:
            str: File content
        
        Raises:
            FleeksResourceNotFoundError: If file doesn't exist
        
        Example:
            >>> content = await workspace.files.read("README.md")
            >>> print(content)
        """
        params = {
            'path': path,
            'encoding': encoding
        }
        
        try:
            response = await self.client._make_request(
                'GET',
                f'/api/v1/sdk/files/{self.project_id}/content',
                params=params
            )
            return response['content']
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(f"File not found: {path}")
            raise
    
    async def read_binary(
        self,
        path: str
    ) -> bytes:
        """
        Read binary file content.
        
        GET /api/v1/sdk/files/{project_id}/content (binary mode)
        
        Args:
            path: File path relative to workspace root
        
        Returns:
            bytes: File content as bytes
        
        Example:
            >>> data = await workspace.files.read_binary("image.png")
            >>> with open("local_image.png", "wb") as f:
            ...     f.write(data)
        """
        params = {
            'path': path,
            'binary': True
        }
        
        response = await self.client._make_request(
            'GET',
            f'/api/v1/sdk/files/{self.project_id}/content',
            params=params
        )
        return response['content'].encode('latin1')  # Backend sends base64
    
    async def update(
        self,
        path: str,
        content: str,
        encoding: str = "utf-8",
        create_if_missing: bool = False
    ) -> FileInfo:
        """
        Update file content.
        
        PUT /api/v1/sdk/files/{project_id}/content
        
        Args:
            path: File path relative to workspace root
            content: New file content
            encoding: Text encoding (default: utf-8)
            create_if_missing: Create file if it doesn't exist
        
        Returns:
            FileInfo: Updated file information
        
        Example:
            >>> file = await workspace.files.update(
            ...     path="config.json",
            ...     content='{"debug": true}'
            ... )
        """
        data = {
            'path': path,
            'content': content,
            'encoding': encoding,
            'create_if_missing': create_if_missing
        }
        
        response = await self.client._make_request(
            'PUT',
            f'/api/v1/sdk/files/{self.project_id}/content',
            json=data
        )
        return FileInfo.from_dict(response)
    
    async def delete(self, path: str) -> None:
        """
        Delete a file.
        
        DELETE /api/v1/sdk/files/{project_id}/content
        
        Args:
            path: File path relative to workspace root
        
        Raises:
            FleeksResourceNotFoundError: If file doesn't exist
        
        Example:
            >>> await workspace.files.delete("temp.txt")
        """
        params = {'path': path}
        
        try:
            await self.client._make_request(
                'DELETE',
                f'/api/v1/sdk/files/{self.project_id}/content',
                params=params
            )
        except FleeksAPIError as e:
            if e.status_code == 404:
                raise FleeksResourceNotFoundError(f"File not found: {path}")
            raise
    
    async def mkdir(
        self,
        path: str,
        parents: bool = True,
        permissions: Optional[str] = None
    ) -> FileInfo:
        """
        Create a directory.
        
        POST /api/v1/sdk/files/{project_id}/directories
        
        Args:
            path: Directory path relative to workspace root
            parents: Create parent directories if needed (like mkdir -p)
            permissions: Directory permissions (e.g., "0755")
        
        Returns:
            FileInfo: Created directory information
        
        Example:
            >>> dir_info = await workspace.files.mkdir("src/components/ui")
        """
        data = {
            'path': path,
            'parents': parents
        }
        if permissions:
            data['permissions'] = permissions
        
        response = await self.client._make_request(
            'POST',
            f'/api/v1/sdk/files/{self.project_id}/directories',
            json=data
        )
        return FileInfo.from_dict(response)
    
    async def upload(
        self,
        path: str,
        file: Union[str, Path, BinaryIO],
        overwrite: bool = False
    ) -> FileInfo:
        """
        Upload a file.
        
        POST /api/v1/sdk/files/{project_id}/upload
        
        Args:
            path: Destination path in workspace
            file: File to upload (path string, Path object, or file-like object)
            overwrite: Overwrite if file exists
        
        Returns:
            FileInfo: Uploaded file information
        
        Example:
            >>> # Upload from local path
            >>> file = await workspace.files.upload(
            ...     path="data.csv",
            ...     file="./local_data.csv"
            ... )
            >>> 
            >>> # Upload from file object
            >>> with open("image.png", "rb") as f:
            ...     file = await workspace.files.upload("assets/logo.png", f)
        """
        # Read file content
        if isinstance(file, (str, Path)):
            with open(file, 'rb') as f:
                file_content = f.read()
        else:
            file_content = file.read()
        
        # Send as multipart/form-data
        files = {
            'file': (Path(path).name, file_content)
        }
        data = {
            'path': path,
            'overwrite': overwrite
        }
        
        response = await self.client._make_request(
            'POST',
            f'/api/v1/sdk/files/{self.project_id}/upload',
            data=data,
            files=files
        )
        return FileInfo.from_dict(response)
    
    async def get_info(self, path: str) -> FileInfo:
        """
        Get file or directory information.
        
        Args:
            path: File/directory path
        
        Returns:
            FileInfo: File metadata
        
        Example:
            >>> info = await workspace.files.get_info("src/main.py")
            >>> print(f"Size: {info.size_bytes} bytes")
            >>> print(f"Modified: {info.modified_at}")
        """
        listing = await self.list(path=path)
        if listing.total_count == 0:
            raise FleeksResourceNotFoundError(f"Path not found: {path}")
        return listing.files[0]
