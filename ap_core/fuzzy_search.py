"""
Fuzzy Search Module for AutoPahe
=================================
Provides intelligent search capabilities with typo tolerance and smart suggestions.
Uses Levenshtein distance algorithm for fuzzy string matching.

Author: AutoPahe Development Team
Date: 2024-11-22
"""

import re
from typing import List, Tuple, Optional, Dict
from difflib import SequenceMatcher, get_close_matches
import logging

logger = logging.getLogger(__name__)


class FuzzySearchEngine:
    """
    Advanced fuzzy search engine with typo tolerance and smart suggestions.
    
    Features:
        - Typo correction (e.g., "deth not" → "death note")
        - Genre-based search filtering
        - Year range filtering
        - Search history and suggestions
        - Confidence scoring for matches
    """
    
    def __init__(self, threshold: float = 0.6):
        """
        Initialize the fuzzy search engine.
        
        Args:
            threshold: Minimum similarity score (0.0 to 1.0) for matches
        """
        self.threshold = threshold
        self.search_history: List[str] = []
        self.common_corrections: Dict[str, str] = {
            # Common anime title typos
            'deth note': 'death note',
            'atack on titan': 'attack on titan',
            'one peace': 'one piece',
            'naruto shipuden': 'naruto shippuden',
            'demon slayer': 'kimetsu no yaiba',
            'full metal': 'fullmetal',
            'cowboy bebop': 'cowboy bebop',
            'steinz gate': 'steins gate',
            'code geas': 'code geass',
            'hunter hunter': 'hunter x hunter',
            'fairy tale': 'fairy tail',
            'black clove': 'black clover',
            'tokyo ghol': 'tokyo ghoul',
            'sword art': 'sword art online',
            'my hero': 'boku no hero academia',
        }
    
    def preprocess_query(self, query: str) -> str:
        """
        Preprocess search query for better matching.
        
        Args:
            query: Raw search query
            
        Returns:
            Cleaned and normalized query string
        """
        # Convert to lowercase and strip whitespace
        query = query.lower().strip()
        
        # Remove multiple spaces
        query = re.sub(r'\s+', ' ', query)
        
        # Apply common corrections
        for typo, correction in self.common_corrections.items():
            if typo in query:
                query = query.replace(typo, correction)
                logger.debug(f"Applied correction: '{typo}' → '{correction}'")
        
        return query
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity score between two strings.
        
        Args:
            str1: First string
            str2: Second string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Use SequenceMatcher for similarity calculation
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def fuzzy_search(self, query: str, anime_list: List[Dict]) -> List[Dict]:
        """
        Perform fuzzy search on anime list with typo tolerance.
        
        Args:
            query: Search query (may contain typos)
            anime_list: List of anime dictionaries from search results
            
        Returns:
            List of matched anime sorted by relevance
        """
        # Preprocess the query
        processed_query = self.preprocess_query(query)
        
        # Store search in history
        if processed_query not in self.search_history:
            self.search_history.append(processed_query)
        
        # Calculate similarity scores for all anime
        scored_results = []
        for anime in anime_list:
            title = anime.get('title', '').lower()
            
            # Direct substring match gets highest score
            if processed_query in title:
                score = 1.0
            else:
                # Calculate fuzzy similarity
                score = self.calculate_similarity(processed_query, title)
                
                # Bonus for word matches
                query_words = set(processed_query.split())
                title_words = set(title.split())
                word_overlap = len(query_words & title_words) / len(query_words) if query_words else 0
                score = (score * 0.7) + (word_overlap * 0.3)
            
            # Only include results above threshold
            if score >= self.threshold:
                scored_results.append((anime, score))
        
        # Sort by score (highest first)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return sorted anime list
        return [anime for anime, _ in scored_results]
    
    def suggest_corrections(self, query: str, anime_titles: List[str]) -> List[str]:
        """
        Suggest corrections for a search query based on available titles.
        
        Args:
            query: Search query that may contain typos
            anime_titles: List of valid anime titles
            
        Returns:
            List of suggested corrections
        """
        processed_query = self.preprocess_query(query)
        
        # Get close matches using difflib
        suggestions = get_close_matches(
            processed_query,
            anime_titles,
            n=5,
            cutoff=self.threshold
        )
        
        return suggestions
    
    def extract_filters(self, query: str) -> Tuple[str, Optional[str], Optional[Tuple[int, int]]]:
        """
        Extract genre and year filters from search query.
        
        Args:
            query: Search query with potential filters
            
        Returns:
            Tuple of (clean_query, genre_filter, year_range)
        """
        # Extract year range (e.g., "2018-2022")
        year_pattern = r'\b(19\d{2}|20\d{2})(?:[-–](19\d{2}|20\d{2}))?\b'
        year_match = re.search(year_pattern, query)
        
        year_range = None
        if year_match:
            start_year = int(year_match.group(1))
            end_year = int(year_match.group(2)) if year_match.group(2) else start_year
            year_range = (start_year, end_year)
            # Remove year from query
            query = re.sub(year_pattern, '', query).strip()
        
        # Extract genre keywords
        genres = [
            'action', 'adventure', 'comedy', 'drama', 'ecchi', 'fantasy',
            'horror', 'magic', 'mecha', 'music', 'mystery', 'psychological',
            'romance', 'sci-fi', 'slice of life', 'sports', 'supernatural',
            'thriller', 'shounen', 'shoujo', 'seinen', 'josei', 'isekai'
        ]
        
        genre_filter = None
        for genre in genres:
            if genre in query.lower():
                genre_filter = genre
                # Remove genre from query
                query = re.sub(rf'\b{genre}\b', '', query, flags=re.IGNORECASE).strip()
                break
        
        return query, genre_filter, year_range
    
    def get_search_suggestions(self) -> List[str]:
        """
        Get search suggestions based on history.
        
        Returns:
            List of recent search queries
        """
        # Return last 10 unique searches
        return list(self.search_history[-10:])
    
    def clear_history(self) -> None:
        """Clear search history."""
        self.search_history.clear()
        logger.info("Search history cleared")


# Global fuzzy search engine instance
fuzzy_engine = FuzzySearchEngine()


def fuzzy_search_anime(query: str, anime_list: List[Dict], 
                       enable_fuzzy: bool = True,
                       threshold: float = 0.6) -> Tuple[List[Dict], str]:
    """
    Convenience function for fuzzy searching anime.
    
    Args:
        query: Search query (may contain typos)
        anime_list: List of anime from search results
        enable_fuzzy: Enable fuzzy matching
        threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (filtered_results, corrected_query)
    """
    if not enable_fuzzy:
        # Simple substring search if fuzzy is disabled
        query_lower = query.lower()
        results = [a for a in anime_list if query_lower in a.get('title', '').lower()]
        return results, query
    
    # Use fuzzy search engine
    fuzzy_engine.threshold = threshold
    
    # Extract filters from query
    clean_query, genre_filter, year_range = fuzzy_engine.extract_filters(query)
    
    # Perform fuzzy search
    results = fuzzy_engine.fuzzy_search(clean_query, anime_list)
    
    # Apply additional filters if present
    if genre_filter:
        # Filter by genre (would need genre data in anime dict)
        logger.info(f"Genre filter detected: {genre_filter}")
    
    if year_range:
        start_year, end_year = year_range
        results = [a for a in results 
                  if start_year <= a.get('year', 0) <= end_year]
        logger.info(f"Year filter applied: {start_year}-{end_year}")
    
    # Get the corrected query
    corrected = fuzzy_engine.preprocess_query(clean_query)
    
    return results, corrected
