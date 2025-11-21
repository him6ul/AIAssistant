"""
GitHub API client for repository and issue management.
"""

import os
from typing import Optional, Dict, Any, List
from github import Github
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Global GitHub client instance
_github_client: Optional[Github] = None


class GitHubClient:
    """
    GitHub API client for accessing repositories and issues.
    """
    
    def __init__(self, access_token: str):
        """
        Initialize GitHub client.
        
        Args:
            access_token: GitHub personal access token
        """
        self.client = Github(access_token)
        self.user = self.client.get_user()
        logger.info(f"GitHub client initialized for user: {self.user.login}")
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Get authenticated user information.
        
        Returns:
            User information dictionary
        """
        return {
            "login": self.user.login,
            "name": self.user.name,
            "email": self.user.email,
            "bio": self.user.bio,
            "public_repos": self.user.public_repos,
            "followers": self.user.followers,
            "following": self.user.following
        }
    
    def get_repositories(self, username: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get repositories for a user.
        
        Args:
            username: GitHub username (defaults to authenticated user)
        
        Returns:
            List of repository information
        """
        try:
            if username:
                user = self.client.get_user(username)
            else:
                user = self.user
            
            repos = []
            for repo in user.get_repos():
                repos.append({
                    "name": repo.name,
                    "full_name": repo.full_name,
                    "description": repo.description,
                    "language": repo.language,
                    "stars": repo.stargazers_count,
                    "forks": repo.forks_count,
                    "private": repo.private,
                    "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                    "url": repo.html_url
                })
            
            logger.info(f"Retrieved {len(repos)} repositories for {user.login}")
            return repos
        except Exception as e:
            logger.error(f"Failed to get repositories: {e}")
            return []
    
    def get_repository(self, repo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific repository.
        
        Args:
            repo_name: Repository name (format: owner/repo or just repo for user's repo)
        
        Returns:
            Repository information or None
        """
        try:
            if "/" not in repo_name:
                repo = self.user.get_repo(repo_name)
            else:
                repo = self.client.get_repo(repo_name)
            
            return {
                "name": repo.name,
                "full_name": repo.full_name,
                "description": repo.description,
                "language": repo.language,
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "watchers": repo.watchers_count,
                "open_issues": repo.open_issues_count,
                "private": repo.private,
                "created_at": repo.created_at.isoformat() if repo.created_at else None,
                "updated_at": repo.updated_at.isoformat() if repo.updated_at else None,
                "url": repo.html_url,
                "clone_url": repo.clone_url
            }
        except Exception as e:
            logger.error(f"Failed to get repository {repo_name}: {e}")
            return None
    
    def get_issues(self, repo_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """
        Get issues for a repository.
        
        Args:
            repo_name: Repository name (format: owner/repo)
            state: Issue state ('open', 'closed', 'all')
        
        Returns:
            List of issues
        """
        try:
            if "/" not in repo_name:
                repo = self.user.get_repo(repo_name)
            else:
                repo = self.client.get_repo(repo_name)
            
            issues = []
            for issue in repo.get_issues(state=state):
                issues.append({
                    "number": issue.number,
                    "title": issue.title,
                    "body": issue.body,
                    "state": issue.state,
                    "user": issue.user.login if issue.user else None,
                    "labels": [label.name for label in issue.labels],
                    "created_at": issue.created_at.isoformat() if issue.created_at else None,
                    "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                    "url": issue.html_url
                })
            
            logger.info(f"Retrieved {len(issues)} {state} issues from {repo_name}")
            return issues
        except Exception as e:
            logger.error(f"Failed to get issues from {repo_name}: {e}")
            return []
    
    def create_issue(self, repo_name: str, title: str, body: str = "", labels: List[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new issue in a repository.
        
        Args:
            repo_name: Repository name (format: owner/repo)
            title: Issue title
            body: Issue body/description
            labels: List of label names
        
        Returns:
            Created issue information or None
        """
        try:
            if "/" not in repo_name:
                repo = self.user.get_repo(repo_name)
            else:
                repo = self.client.get_repo(repo_name)
            
            issue = repo.create_issue(title=title, body=body, labels=labels or [])
            
            logger.info(f"Created issue #{issue.number} in {repo_name}")
            return {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "url": issue.html_url
            }
        except Exception as e:
            logger.error(f"Failed to create issue in {repo_name}: {e}")
            return None
    
    def get_pull_requests(self, repo_name: str, state: str = "open") -> List[Dict[str, Any]]:
        """
        Get pull requests for a repository.
        
        Args:
            repo_name: Repository name (format: owner/repo)
            state: PR state ('open', 'closed', 'all')
        
        Returns:
            List of pull requests
        """
        try:
            if "/" not in repo_name:
                repo = self.user.get_repo(repo_name)
            else:
                repo = self.client.get_repo(repo_name)
            
            prs = []
            for pr in repo.get_pulls(state=state):
                prs.append({
                    "number": pr.number,
                    "title": pr.title,
                    "body": pr.body,
                    "state": pr.state,
                    "user": pr.user.login if pr.user else None,
                    "merged": pr.merged,
                    "created_at": pr.created_at.isoformat() if pr.created_at else None,
                    "updated_at": pr.updated_at.isoformat() if pr.updated_at else None,
                    "url": pr.html_url
                })
            
            logger.info(f"Retrieved {len(prs)} {state} pull requests from {repo_name}")
            return prs
        except Exception as e:
            logger.error(f"Failed to get pull requests from {repo_name}: {e}")
            return []


def get_github_client() -> Optional[GitHubClient]:
    """
    Get or create the global GitHub client instance.
    
    Returns:
        GitHubClient instance or None if not configured
    """
    global _github_client
    
    if _github_client is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        access_token = os.getenv("GITHUB_ACCESS_TOKEN")
        
        if not access_token:
            logger.warning("GitHub access token not configured. GitHub features will be disabled.")
            return None
        
        try:
            _github_client = GitHubClient(access_token)
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            return None
    
    return _github_client

