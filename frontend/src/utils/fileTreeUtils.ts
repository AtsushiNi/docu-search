import type { FileItem, TreeNode } from '../types';

/**
 * 文字列タイトルかどうかをチェックする関数
 */
export const isStringTitle = (title: string | React.ReactNode): title is string => {
  return typeof title === 'string';
};

/**
 * ツリーノードをコンパクト化する関数
 * 小フォルダが1つだけの場合は結合して表示する
 */
export const compactTreeNodes = (node: TreeNode): TreeNode => {
  if (node.children && node.children.length === 1 && !node.children[0].isLeaf) {
    const child = compactTreeNodes(node.children[0]);
    if (isStringTitle(node.title) && isStringTitle(child.title)) {
      return {
        title: `${node.title}/${child.title}`,
        key: node.key,
        url: child.url,
        isLeaf: child.isLeaf,
        children: child.children
      };
    }
  }
  return {
    ...node,
    children: node.children ? node.children.map(compactTreeNodes) : undefined
  };
};

/**
 * URLスキームを抽出する関数
 */
export const extractUrlScheme = (path: string): {scheme: string | null, path: string} => {
  const urlMatch = path.match(/^((https?|svn):\/\/)(.*)/);
  return {
    scheme: urlMatch ? urlMatch[1] : null,
    path: urlMatch ? urlMatch[3] : path
  };
};

/**
 * ファイルリストからツリーデータを構築するユーティリティ関数
 * FileTree.tsx と同じロジックを使用
 */
export const buildTreeData = (files: FileItem[]): TreeNode[] => {
  const root: TreeNode = { 
    title: 'Root', 
    key: 'root', 
    url: '', 
    isLeaf: false, 
    children: [] 
  };
  
  files.forEach((file) => {
    const {scheme, path: cleanPath} = extractUrlScheme(file.url);
    const parts = cleanPath.split('/').filter(part => part !== '');
    if (scheme && parts.length > 0) {
      parts[0] = scheme + parts[0];
    }
    let current = root;
    
    parts.forEach((part, i) => {
      const existing = current.children?.find(child => child.title === part);
      
      if (existing) {
        current = existing;
      } else {
        const nodePath = parts.slice(0, i + 1).join('/');
        const newNode: TreeNode = {
          title: part,
          key: i === parts.length - 1 ? file.id : `${file.id}-${i}`,
          url: nodePath,
          id: i === parts.length - 1 ? file.id : undefined,
          isLeaf: i === parts.length - 1,
          children: []
        };
        
        if (!current.children) {
          current.children = [];
        }
        
        current.children.push(newNode);
        current = newNode;
      }
    });
  });
  
  const mergedChildren = (root.children || []).map(compactTreeNodes);
  return mergedChildren;
};

/**
 * ファイルリストを検索テキストでフィルタリングする関数
 */
export const filterFiles = (files: FileItem[], searchText: string): FileItem[] => {
  if (!searchText.trim()) {
    return files;
  }

  const lowerSearchText = searchText.toLowerCase();
  return files.filter(file =>
    (file.url?.toLowerCase() || '').includes(lowerSearchText) ||
    (file.filename?.toLowerCase() || '').includes(lowerSearchText)
  );
};
