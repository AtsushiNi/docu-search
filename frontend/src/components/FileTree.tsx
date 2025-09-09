import { useState, useEffect, useMemo } from 'react';
import { Tree, Input } from 'antd';
import { getFileList } from '../services/api';
import { 
  isStringTitle, 
  buildTreeData 
} from '../utils/fileTreeUtils';
import type { TreeNode } from '../types';

const { Search } = Input;

type FileTreeProps = unknown

const FileTree: React.FC<FileTreeProps> = () => {
  const [fileTree, setFileTree] = useState<TreeNode[]>([]);
  const [expandedKeys, setExpandedKeys] = useState<string[]>([]);
  const [searchValue, setSearchValue] = useState('');
  const [autoExpandParent, setAutoExpandParent] = useState(true);


  useEffect(() => {
    const fetchFiles = async () => {
      try {
        const files = await getFileList();
        const treeData = buildTreeData(files.map((f: {url: string, id: string}) => ({url: f.url, id: f.id, filename: f.url.split('/').pop()})));
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
        selectable={false}
        treeData={processedTreeData}
        expandedKeys={expandedKeys}
        autoExpandParent={autoExpandParent}
        onExpand={keys => {
          setExpandedKeys(keys as string[]);
          setAutoExpandParent(false);
        }}
        onClick={(_event, node) => {
          if (node.isLeaf && node.id) {
            // 詳細ページに遷移
            window.open(`/documents/${node.id}?view=markdown`, '_blank');
          } else {
            // フォルダノードのクリック処理
            const key = node.key;
            setExpandedKeys(prev => 
              prev.includes(key) 
                ? prev.filter(k => k !== key) // 折り畳み
                : [...prev, key] // 展開
            );
            setAutoExpandParent(false);
          }
        }}
      />
    </div>
  );
};

export default FileTree;
