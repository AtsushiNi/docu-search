export interface SearchResult {
  _id: string;
  _source: {
    title: string;
    name: string;
    content: string;
    url: string;
    last_modified: string;
  };
}
