"""
OneNote ingestion via Microsoft Graph API.
"""

import html
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from app.ingestion.ms_graph_client import get_graph_client
from app.tasks.storage import get_task_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class OneNoteIngestor:
    """
    Ingests OneNote pages via Microsoft Graph API.
    """
    
    def __init__(self):
        """Initialize OneNote ingestor."""
        self.graph_client = get_graph_client()
        self.storage = get_task_storage()
        self._processed_pages: set = set()
    
    def _html_to_text(self, html_content: str) -> str:
        """
        Convert OneNote HTML to clean text.
        
        Args:
            html_content: OneNote HTML content
        
        Returns:
            Clean text
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text and clean up
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            logger.error(f"Failed to convert HTML to text: {e}")
            return html_content
    
    async def get_notebooks(self) -> List[Dict[str, Any]]:
        """
        Get all OneNote notebooks.
        
        Returns:
            List of notebook objects
        """
        try:
            response = await self.graph_client.make_request("GET", "/me/onenote/notebooks")
            notebooks = response.get("value", [])
            logger.info(f"Found {len(notebooks)} notebooks")
            return notebooks
        except Exception as e:
            logger.error(f"Failed to get notebooks: {e}")
            return []
    
    async def get_sections(self, notebook_id: str) -> List[Dict[str, Any]]:
        """
        Get sections in a notebook.
        
        Args:
            notebook_id: Notebook ID
        
        Returns:
            List of section objects
        """
        try:
            response = await self.graph_client.make_request("GET", f"/me/onenote/notebooks/{notebook_id}/sections")
            sections = response.get("value", [])
            logger.info(f"Found {len(sections)} sections in notebook {notebook_id}")
            return sections
        except Exception as e:
            logger.error(f"Failed to get sections: {e}")
            return []
    
    async def get_pages(self, section_id: str) -> List[Dict[str, Any]]:
        """
        Get pages in a section.
        
        Args:
            section_id: Section ID
        
        Returns:
            List of page objects
        """
        try:
            response = await self.graph_client.make_request("GET", f"/me/onenote/sections/{section_id}/pages")
            pages = response.get("value", [])
            logger.info(f"Found {len(pages)} pages in section {section_id}")
            return pages
        except Exception as e:
            logger.error(f"Failed to get pages: {e}")
            return []
    
    async def get_page_content(self, page_id: str) -> Optional[str]:
        """
        Get content of a specific page.
        
        Args:
            page_id: Page ID
        
        Returns:
            Page content as text
        """
        try:
            response = await self.graph_client.make_request("GET", f"/me/onenote/pages/{page_id}/content")
            
            # Response is HTML content
            html_content = response if isinstance(response, str) else response.get("content", "")
            
            # Convert HTML to text
            text_content = self._html_to_text(html_content)
            
            return text_content
        except Exception as e:
            logger.error(f"Failed to get page content: {e}")
            return None
    
    async def ingest_all(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Ingest all OneNote pages.
        
        Args:
            max_pages: Maximum number of pages to ingest
        
        Returns:
            List of ingested page data
        """
        logger.info("Starting OneNote ingestion")
        
        ingested_pages = []
        page_count = 0
        
        try:
            # Get all notebooks
            notebooks = await self.get_notebooks()
            
            for notebook in notebooks:
                if page_count >= max_pages:
                    break
                
                notebook_id = notebook.get("id")
                notebook_name = notebook.get("displayName", "Unknown")
                
                # Get sections
                sections = await self.get_sections(notebook_id)
                
                for section in sections:
                    if page_count >= max_pages:
                        break
                    
                    section_id = section.get("id")
                    section_name = section.get("displayName", "Unknown")
                    
                    # Get pages
                    pages = await self.get_pages(section_id)
                    
                    for page in pages:
                        if page_count >= max_pages:
                            break
                        
                        page_id = page.get("id")
                        
                        # Skip if already processed
                        if page_id in self._processed_pages:
                            continue
                        
                        # Get page content
                        content = await self.get_page_content(page_id)
                        
                        if content:
                            ingested_pages.append({
                                "id": page_id,
                                "title": page.get("title", "Untitled"),
                                "content": content,
                                "notebook": notebook_name,
                                "section": section_name,
                                "last_modified": page.get("lastModifiedDateTime")
                            })
                            
                            self._processed_pages.add(page_id)
                            page_count += 1
                            
                            # Log ingestion
                            await self.storage.log_ingestion(
                                source_type="onenote",
                                source_id=page_id,
                                status="success"
                            )
            
            logger.info(f"Ingested {len(ingested_pages)} OneNote pages")
            return ingested_pages
        
        except Exception as e:
            logger.error(f"OneNote ingestion failed: {e}")
            return ingested_pages
    
    async def ingest_new_and_updated(self, max_pages: int = 100) -> List[Dict[str, Any]]:
        """
        Ingest only new and updated pages.
        
        Args:
            max_pages: Maximum number of pages to check
        
        Returns:
            List of new/updated page data
        """
        # For now, just ingest all and filter by processed set
        # In production, you'd check lastModifiedDateTime against stored timestamps
        return await self.ingest_all(max_pages)

