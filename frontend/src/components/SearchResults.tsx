import type { SearchResult } from '../types';
import React from 'react';
import { Button, Card } from 'antd';
import { DownloadOutlined } from '@ant-design/icons';

interface SearchResultsProps {
  results: SearchResult[];
}

const SearchResults: React.FC<SearchResultsProps> = ({ results }) => {
  if (results.length === 0) {
    return <div className="text-gray-500">No results found</div>;
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <Card 
          key={result._id}
          hoverable
          className="w-full"
          title={result._source.name}
          extra={<Button 
            icon={<DownloadOutlined/>} 
            color='default' 
            variant='filled'
            onClick={() => window.open(result._source.url)}
          />}
        >
          <Card.Meta
            description={
              <>
                <p className="text-sm text-gray-600">{result._source.url}</p>
                <p className="mt-2 text-gray-800 line-clamp-2">
                  {/* {result._source.content} */}
                </p>
                <p className="text-xs text-gray-500 mt-2">
                  Last modified: {new Date(result._source.last_modified).toLocaleString()}
                </p>
              </>
            }
          />
        </Card>
      ))}
    </div>
  );
};

export default SearchResults;
