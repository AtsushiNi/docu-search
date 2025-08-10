import { useState } from 'react';
import { searchDocuments } from '../services/api';
import SearchResults from './SearchResults';
import type { SearchResult } from '../types';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const data = await searchDocuments(query);
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div style={{ marginLeft: 200, marginRight: 200 }}>
      <div className="search-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="検索キーワードを入力"
          className="search-input"
        />
        <button 
          onClick={handleSearch}
          disabled={isSearching}
          className="search-button"
        >
          {isSearching ? '検索中...' : '検索'}
        </button>
      </div>
      
      <SearchResults results={results} />
    </div>
  );
};

export default SearchPage;
