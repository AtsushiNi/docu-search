import { useState, useEffect, useMemo } from 'react';
import { Tree, Input } from 'antd';
import { getFileList } from '../services/api';

interface TreeNode {
  title: string | React.ReactNode;
  key: string;
  url: string;
  isLeaf: boolean;
  children?: TreeNode[];
}

const { Search } = Input;

type FileTreeProps = unknown

const FileTree: React.FC<FileTreeProps> = () => {
  const [fileTree, setFileTree] = useState<TreeNode[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  const isStringTitle = (title: string | React.ReactNode): title is string => {
    return typeof title === 'string';
  };

  const compactTreeNodes = (node: TreeNode): TreeNode => {
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

  const extractUrlScheme = (path: string): {scheme: string | null, path: string} => {
    const urlMatch = path.match(/^((https?|svn):\/\/)(.*)/);
    return {
      scheme: urlMatch ? urlMatch[1] : null,
      path: urlMatch ? urlMatch[3] : path
    };
  };

  const buildFileTree = (paths: string[]): TreeNode[] => {
    const root: TreeNode = { title: 'Root', key: 'root', url: '', isLeaf: false, children: [] };
    
    paths.forEach((path, index) => {
      const {scheme, path: cleanPath} = extractUrlScheme(path);
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
            key: `${index}-${i}`,
            url: nodePath,
            isLeaf: i === parts.length - 1
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

  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const files = await getFileList();
        const treeData = buildFileTree(files);
        setFileTree(treeData);
      } catch (error) {
        console.error('Failed to load files:', error);
      }
    };

    fetchFiles();
  }, []);

  const dataList = useMemo(() => {
    const list: { key: string; title: string }[] = [];
    const generateList = (data: TreeNode[]) => {
      for (let i = 0; i < data.length; i++) {
        const node = data[i];
        const { key, title } = node;
        if (isStringTitle(title)) {
          list.push({ key, title });
        }
        if (node.children) {
          generateList(node.children);
        }
      }
    };
    generateList(fileTree);
    return list;
  }, [fileTree]);

  const getParentKey = (key: string, tree: TreeNode[]): string => {
    let parentKey = '';
    for (let i = 0; i < tree.length; i++) {
      const node = tree[i];
      if (node.children) {
        if (node.children.some(item => item.key === key)) {
          parentKey = node.key;
        } else {
          const foundKey = getParentKey(key, node.children);
          if (foundKey) {
            parentKey = foundKey;
          }
        }
      }
    }
    return parentKey;
  };

  const onSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = e.target;
    const newExpandedKeys = dataList
      .map(item => {
        if (item.title.toLowerCase().includes(value.toLowerCase())) {
          return getParentKey(item.key, fileTree);
        }
        return null;
      })
      .filter((item, i, self): item is string => !!item && self.indexOf(item) === i);
    
    setExpandedKeys(newExpandedKeys);
    setSearchValue(value);
    setAutoExpandParent(true);
  };

  const processedTreeData = useMemo(() => {
    const loop = (data: TreeNode[]): TreeNode[] =>
      data.map(item => {
        if (!isStringTitle(item.title)) {
          return item;
        }

        const strTitle = item.title;
        const index = strTitle.toLowerCase().indexOf(searchValue.toLowerCase());
        const beforeStr = strTitle.substring(0, index);
        const searchStr = strTitle.substring(index, index + searchValue.length)
        const afterStr = strTitle.slice(index + searchValue.length);
        const title =
          index > -1 ? (
            <span>
              {beforeStr}
              <span style={{ color: '#f50' }}>{searchStr}</span>
              {afterStr}
            </span>
          ) : (
            <span>{strTitle}</span>
          );

        if (item.children) {
          return { ...item, title, children: loop(item.children) };
        }

        return {
          ...item,
          title
        };
      });

    return loop(fileTree);
  }, [fileTree, searchValue]);

  return (
    <div style={{ padding: '16px' }}>
      <Search 
        style={{ marginBottom: 8 }} 
        placeholder="Search files" 
        onChange={onSearchChange}
      />
      <Tree<TreeNode>
        treeData={processedTreeData}
        expandedKeys={expandedKeys}
        autoExpandParent={autoExpandParent}
        onExpand={keys => {
          setExpandedKeys(keys as string[]);
          setAutoExpandParent(false);
        }}
        onSelect={(_, info) => {
          const node = info.node as TreeNode;
          if (node.url) {
            window.open(node.url, '_blank');
          }
        }}
      />
    </div>
  );
};

export default FileTree;
