#!/usr/bin/env python3
"""
Comprehensive Test Suite for AutoPahe
======================================
Tests all major features including caching, fuzzy search, resume system, and collection manager.

Author: AutoPahe Development Team
Date: 2024-11-22
"""

import os
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ap_core.cache import cache_get, cache_set, cache_clear, get_cache_stats
from ap_core.fuzzy_search import FuzzySearchEngine, fuzzy_search_anime
from ap_core.resume_manager import SmartResumeManager, DownloadState
from ap_core.collection_manager import CollectionManager, WatchStatus, AnimeEntry


def print_test_header(test_name):
    """Print a formatted test header."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")


def test_cache_functionality():
    """Test cache storage, retrieval, and stats."""
    print_test_header("Cache System")
    
    # Clear cache first
    cache_clear()
    print("✓ Cache cleared")
    
    # Test cache set and get
    test_url = "https://test.com/api?q=test"
    test_data = b'{"data": [{"title": "Test Anime", "episodes": 12}]}'
    
    cache_set(test_url, test_data)
    print("✓ Data cached successfully")
    
    # Retrieve from cache
    cached = cache_get(test_url, max_age_hours=24)
    assert cached == test_data, "Cache retrieval failed"
    print("✓ Data retrieved from cache correctly")
    
    # Test cache stats
    stats = get_cache_stats()
    assert stats['count'] > 0, "Cache should have entries"
    print(f"✓ Cache stats: {stats['count']} files, {stats['size_mb']:.2f} MB")
    
    # Test cache expiry
    expired = cache_get(test_url, max_age_hours=0)
    assert expired is None, "Expired cache should return None"
    print("✓ Cache expiry working correctly")
    
    return True


def test_fuzzy_search():
    """Test fuzzy search with typo correction."""
    print_test_header("Fuzzy Search Engine")
    
    engine = FuzzySearchEngine(threshold=0.6)
    
    # Test typo correction
    test_cases = [
        ("deth note", "death note"),
        ("atack on titan", "attack on titan"),
        ("one peace", "one piece"),
        ("naruto shipuden", "naruto shippuden"),
    ]
    
    for typo, expected in test_cases:
        corrected = engine.preprocess_query(typo)
        assert expected in corrected, f"Failed to correct '{typo}' to '{expected}'"
        print(f"✓ Corrected: '{typo}' → '{corrected}'")
    
    # Test similarity calculation
    similarity = engine.calculate_similarity("death note", "Death Note")
    assert similarity > 0.9, "Similarity should be high for same title"
    print(f"✓ Similarity calculation: {similarity:.2f}")
    
    # Test fuzzy search on anime list
    anime_list = [
        {"title": "Death Note", "episodes": 37, "year": 2006},
        {"title": "One Piece", "episodes": 1000, "year": 1999},
        {"title": "Attack on Titan", "episodes": 87, "year": 2013},
    ]
    
    results = engine.fuzzy_search("deth not", anime_list)
    assert len(results) > 0, "Should find Death Note with typo"
    assert results[0]['title'] == "Death Note", "Death Note should be first result"
    print(f"✓ Fuzzy search found: {results[0]['title']}")
    
    # Test filter extraction
    query, genre, years = engine.extract_filters("action anime 2020-2023")
    assert genre == "action", "Should extract genre"
    assert years == (2020, 2023), "Should extract year range"
    print(f"✓ Filter extraction: genre={genre}, years={years}")
    
    return True


def test_resume_manager():
    """Test download resume system."""
    print_test_header("Resume Manager")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = SmartResumeManager(state_dir=Path(tmpdir))
        
        # Test adding download
        download_id = manager.add_download(
            anime_title="Death Note",
            episode_number="1",
            download_url="https://test.com/download",
            file_path="/tmp/death_note_ep1.mp4",
            quality="720p"
        )
        assert download_id, "Should return download ID"
        print(f"✓ Download added: {download_id}")
        
        # Test progress update
        manager.update_progress(download_id, 1024000, 10240000)
        state = manager.download_states[download_id]
        assert state.downloaded_size == 1024000, "Progress not updated"
        print(f"✓ Progress updated: {state.downloaded_size / 1024000:.1f} MB")
        
        # Test marking as completed
        manager.mark_completed(download_id)
        assert state.status == 'completed', "Status should be completed"
        print("✓ Download marked as completed")
        
        # Test failure and retry
        download_id2 = manager.add_download(
            anime_title="One Piece",
            episode_number="1",
            download_url="https://test.com/download2",
            file_path="/tmp/one_piece_ep1.mp4",
            quality="1080p"
        )
        
        should_retry = manager.mark_failed(download_id2, "Network error")
        assert should_retry, "Should allow retry on first failure"
        assert manager.download_states[download_id2].retry_count == 1
        print(f"✓ Failure handling: retry count = {manager.download_states[download_id2].retry_count}")
        
        # Test resumable downloads
        resumable = manager.get_resumable_downloads()
        assert len(resumable) > 0, "Should have resumable downloads"
        print(f"✓ Found {len(resumable)} resumable downloads")
        
        # Test statistics
        stats = manager.get_download_stats()
        assert stats['total'] == 2, "Should have 2 downloads"
        assert stats['completed'] == 1, "Should have 1 completed"
        print(f"✓ Stats: {stats['total']} total, {stats['completed']} completed")
        
        # Test quality fallback
        fallback = manager.get_fallback_quality(download_id2)
        assert fallback == "720p", "Should fallback to 720p from 1080p"
        print(f"✓ Quality fallback: 1080p → {fallback}")
    
    return True


def test_collection_manager():
    """Test anime collection management."""
    print_test_header("Collection Manager")
    
    # Create temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = CollectionManager(
            collection_dir=Path(tmpdir) / "anime",
            metadata_dir=Path(tmpdir) / "metadata"
        )
        
        # Test adding anime
        entry = manager.add_anime("Death Note", total_episodes=37)
        assert entry.title == "Death Note", "Anime not added correctly"
        print(f"✓ Anime added: {entry.title}")
        
        # Test adding episodes
        for ep in [1, 2, 3]:
            # Create dummy file
            ep_file = Path(tmpdir) / f"death_note_ep{ep}.mp4"
            ep_file.write_text("dummy content")
            
            final_path = manager.add_episode_file(
                "Death Note", ep, str(ep_file), organize=False
            )
            assert final_path, "Episode not added"
        
        entry = manager.collection["Death Note"]
        assert len(entry.downloaded_episodes) == 3, "Episodes not tracked"
        print(f"✓ Episodes added: {sorted(entry.downloaded_episodes)}")
        
        # Test completion percentage
        completion = entry.get_completion_percentage()
        expected = (3 / 37) * 100
        assert abs(completion - expected) < 0.1, "Completion % incorrect"
        print(f"✓ Completion: {completion:.1f}%")
        
        # Test missing episodes
        missing = entry.get_missing_episodes()
        assert 4 in missing and 37 in missing, "Missing episodes incorrect"
        print(f"✓ Missing episodes: {len(missing)} episodes")
        
        # Test watch status update
        manager.update_watch_status("Death Note", WatchStatus.WATCHING, progress=3)
        assert entry.watch_status == WatchStatus.WATCHING
        assert entry.watch_progress == 3
        print(f"✓ Watch status: {entry.watch_status.value}, progress: {entry.watch_progress}")
        
        # Test rating
        entry.rating = 9
        manager.save_collection()
        print(f"✓ Rating set: {entry.rating}/10")
        
        # Test statistics
        stats = manager.get_statistics()
        assert stats['total_anime'] == 1
        assert stats['total_episodes'] == 3
        assert stats['watch_status']['watching'] == 1
        print(f"✓ Collection stats: {stats['total_anime']} anime, {stats['total_episodes']} episodes")
        
        # Test export
        export_path = Path(tmpdir) / "export.json"
        manager.export_collection(str(export_path), format='json')
        assert export_path.exists(), "Export file not created"
        
        with open(export_path) as f:
            exported = json.load(f)
            assert 'collection' in exported
            assert 'Death Note' in exported['collection']
        print(f"✓ Collection exported to JSON")
        
        # Test duplicate detection (create duplicate)
        dup_file = Path(tmpdir) / "death_note_ep1_copy.mp4"
        dup_file.write_text("dummy content")  # Same content as ep1
        manager.add_episode_file("Death Note", 1, str(dup_file), organize=False)
        
        duplicates = manager.detect_duplicates()
        # Note: duplicates detection is based on file hash, same content = duplicate
        print(f"✓ Duplicate detection: {len(duplicates)} sets found")
        
        # Test sanitize filename
        sanitized = manager.sanitize_filename('Test: Anime <Name> | Part 1')
        assert ':' not in sanitized and '<' not in sanitized
        print(f"✓ Filename sanitization: '{sanitized}'")
    
    return True


def test_integration():
    """Test integration between components."""
    print_test_header("Component Integration")
    
    # Test cache + fuzzy search integration
    test_url = "https://animepahe.si/api?m=search&q=death note"
    test_data = json.dumps({
        "data": [
            {"title": "Death Note", "episodes": 37, "year": 2006, "status": "Finished Airing"},
            {"title": "Death Note: Rewrite", "episodes": 2, "year": 2007, "status": "Finished Airing"}
        ]
    }).encode()
    
    cache_set(test_url, test_data)
    cached = cache_get(test_url, max_age_hours=24)
    
    if cached:
        data = json.loads(cached)
        results, corrected = fuzzy_search_anime("deth not", data['data'], enable_fuzzy=True)
        assert len(results) > 0, "Fuzzy search should find results"
        print(f"✓ Cache + Fuzzy Search: Found {len(results)} results")
    
    # Test resume + collection integration
    with tempfile.TemporaryDirectory() as tmpdir:
        resume_mgr = SmartResumeManager(state_dir=Path(tmpdir) / "resume")
        collection_mgr = CollectionManager(
            collection_dir=Path(tmpdir) / "anime",
            metadata_dir=Path(tmpdir) / "metadata"
        )
        
        # Simulate download workflow
        download_id = resume_mgr.add_download(
            anime_title="Death Note",
            episode_number="1",
            download_url="https://test.com/download",
            file_path=str(Path(tmpdir) / "death_note_ep1.mp4"),
            quality="720p"
        )
        
        # Add to collection
        collection_mgr.add_anime("Death Note", total_episodes=37)
        
        # Create dummy file
        ep_file = Path(tmpdir) / "death_note_ep1.mp4"
        ep_file.write_text("dummy video content")
        
        collection_mgr.add_episode_file("Death Note", 1, str(ep_file), organize=False)
        
        # Mark download complete
        resume_mgr.mark_completed(download_id)
        
        # Verify integration
        assert resume_mgr.download_states[download_id].status == 'completed'
        assert 1 in collection_mgr.collection["Death Note"].downloaded_episodes
        print("✓ Resume + Collection integration working")
    
    return True


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("🚀 AUTOPAHE COMPREHENSIVE TEST SUITE")
    print("="*60)
    
    tests = [
        ("Cache System", test_cache_functionality),
        ("Fuzzy Search", test_fuzzy_search),
        ("Resume Manager", test_resume_manager),
        ("Collection Manager", test_collection_manager),
        ("Integration", test_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, "✅ PASSED"))
            time.sleep(0.5)  # Brief pause between tests
        except Exception as e:
            results.append((test_name, f"❌ FAILED: {str(e)}"))
            import traceback
            traceback.print_exc()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST RESULTS SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        print(f"  {test_name:20s} : {result}")
    
    passed = sum(1 for _, r in results if "PASSED" in r)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"✨ FINAL SCORE: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 ALL TESTS PASSED! The application is working correctly.")
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
