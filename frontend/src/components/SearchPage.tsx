import { useState } from 'react';
import { Input, Button, Radio, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { searchDocuments } from '../services/api';
import SearchResults from './SearchResults';
import type { SearchResult } from '../types';

type SearchType = 'exact' | 'fuzzy';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>('exact');

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    try {
      const data = await searchDocuments(query, searchType);
      setResults(data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div style={{ marginLeft: 200, marginRight: 200 }}>
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <Space.Compact style={{ width: '100%' }}>
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="検索キーワードを入力"
              size="large"
              onPressEnter={handleSearch}
            />
            <Button 
              type="primary" 
              icon={<SearchOutlined />}
              onClick={handleSearch}
              loading={isSearching}
              size="large"
            >
              検索
            </Button>
          </Space.Compact>
          
          <Radio.Group 
            value={searchType} 
            onChange={(e) => setSearchType(e.target.value as SearchType)}
            optionType="button"
            buttonStyle="solid"
          >
            <Radio.Button value="exact">単語検索</Radio.Button>
            <Radio.Button value="fuzzy">あいまい検索</Radio.Button>
          </Radio.Group>
        </Space>
      
      <SearchResults results={results} />
    </div>
  );
};

export default SearchPage;
