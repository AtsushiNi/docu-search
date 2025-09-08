import { useState } from 'react';
import { Input, Button, Radio, Space } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { searchDocuments } from '../services/api';
import SearchResults from './SearchResults';
import type { SearchResult } from '../types';

type SearchType = 'exact' | 'fuzzy';

const SearchPage = () => {
  const [query, setQuery] = useState('');
  const [urlQuery, setUrlQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchType, setSearchType] = useState<SearchType>('exact');

  const handleSearch = async () => {
    if (!query.trim() && !urlQuery.trim()) return;
    setIsSearching(true);
    try {
      const data = await searchDocuments(query, searchType, urlQuery.trim());
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
        <Space size="middle" align="baseline">
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ marginRight: 8, fontWeight: 'bold' }}>検索タイプ:</span>
            <Radio.Group 
              value={searchType} 
              onChange={(e) => setSearchType(e.target.value as SearchType)}
              optionType="button"
              buttonStyle="solid"
            >
              <Radio.Button value="exact">単語検索</Radio.Button>
              <Radio.Button value="fuzzy">あいまい検索</Radio.Button>
            </Radio.Group>
          </div>

          {/* URLフィルターを検索タイプの右側に配置 */}
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <span style={{ marginRight: 8, fontWeight: 'bold' }}>URLフィルター:</span>
            <div style={{ position: 'relative' }}>
              <Input
                value={urlQuery}
                onChange={(e) => setUrlQuery(e.target.value)}
                placeholder="URLに含まれる単語を入力"
                size="large"
                onPressEnter={handleSearch}
                style={{ width: 300 }}
              />
              <span style={{
                position: 'absolute',
                right: 8,
                top: '50%',
                transform: 'translateY(-50%)',
                fontSize: '12px',
                color: '#999',
                backgroundColor: 'white',
                padding: '0 4px'
              }}>
                任意
              </span>
            </div>
          </div>
        </Space>

        {/* メイン検索フィールドとボタン */}
        <Space.Compact style={{ width: '100%' }}>
          <Input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="検索キーワードを入力"
            size="large"
            onPressEnter={handleSearch}
            style={{ flex: 1 }}
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
      </Space>
      
      <SearchResults results={results} />
    </div>
  );
};

export default SearchPage;
