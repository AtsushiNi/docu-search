import React, { useState, useCallback, useEffect } from 'react';
import { Card, Button, Space, Tree, Modal, message } from 'antd';
import { DeleteOutlined, FolderOutlined, FileOutlined } from '@ant-design/icons';
import type { TreeNode, FileItem } from '../types';
import { getFileList, deleteFiles } from '../services/api';
import { buildTreeData } from '../utils/fileTreeUtils';

const FilesPage: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

  // ファイル一覧を取得
  const fetchFiles = useCallback(async () => {
    try {
      const filesData = await getFileList();
      // バックエンドから返される {url, id} を FileItem 形式に変換
      const formattedFiles = filesData.map((file: { url: string; id: string }) => ({
        id: file.id,
        url: file.url,
        filename: file.url.split('/').pop() || file.url,
        is_directory: false
      }));
      setFiles(formattedFiles);
    } catch (error) {
      console.error('ファイル一覧の取得に失敗しました:', error);
      message.error('ファイル一覧の取得に失敗しました');
    }
  }, []);

  // フォルダノード以下のすべてのファイルキーを取得する関数
  const getAllFileKeysFromFolder = useCallback((node: TreeNode, allFileKeys: React.Key[] = []) => {
    if (node.isLeaf) {
      allFileKeys.push(node.key);
    } else if (node.children) {
      node.children.forEach(child => getAllFileKeysFromFolder(child, allFileKeys));
    }
    return allFileKeys;
  }, []);

  // ファイル削除処理
  const handleDelete = useCallback(() => {
    console.log('削除ボタンがクリックされました', { selectedRowKeys });
    
    if (selectedRowKeys.length === 0) {
      message.warning('削除するファイルを選択してください');
      return;
    }

    setIsDeleteModalVisible(true);
  }, [selectedRowKeys]);

  // 削除確認モーダルのOK処理
  const handleDeleteConfirm = useCallback(async () => {
    try {
      // selectedRowKeys（ファイルID）から対応するファイルのIDを取得
      const fileIdsToDelete = selectedRowKeys
        .map(key => {
          const file = files.find(f => f.id === key.toString());
          return file?.id;
        })
        .filter((id): id is string => id !== undefined);

      if (fileIdsToDelete.length === 0) {
        message.warning('削除するファイルが見つかりませんでした');
        return;
      }

      console.log('削除リクエストを送信します:', fileIdsToDelete);
      await deleteFiles(fileIdsToDelete);
      message.success('ファイルを削除しました');
      setSelectedRowKeys([]);
      setIsDeleteModalVisible(false);
      fetchFiles();
    } catch (error) {
      console.error('ファイルの削除に失敗しました:', error);
      message.error('ファイルの削除に失敗しました');
    }
  }, [selectedRowKeys, files, fetchFiles]);

  // 削除確認モーダルのキャンセル処理
  const handleDeleteCancel = useCallback(() => {
    setIsDeleteModalVisible(false);
  }, []);

  useEffect(() => {
    fetchFiles();
  }, [fetchFiles]);


  return (
    <div>
      <Card 
        title="ファイル管理"
        extra={
          <Space>
            <Button 
              type="primary" 
              danger
              icon={<DeleteOutlined />}
              onClick={handleDelete}
              disabled={selectedRowKeys.length === 0}
            >
              選択したファイルを削除
            </Button>
          </Space>
        }
      >
        <Tree
          showLine
          treeData={buildTreeData(files)}
          titleRender={(node: TreeNode) => (
            <Space>
              {node.isLeaf ? <FileOutlined /> : <FolderOutlined />}
              <span>{node.title}</span>
            </Space>
          )}
          style={{ marginBottom: 24 }}
          checkable
          checkedKeys={selectedRowKeys}
          onCheck={(checkedKeys, { node, checked }) => {
            // フォルダが選択された場合、そのフォルダ以下のすべてのファイルを選択
            if (checked && !node.isLeaf) {
              const allFileKeys = getAllFileKeysFromFolder(node);
              setSelectedRowKeys(prev => [...new Set([...prev, ...allFileKeys])]);
            } 
            // フォルダが選択解除された場合、そのフォルダ以下のすべてのファイルを選択解除
            else if (!checked && !node.isLeaf) {
              const allFileKeys = getAllFileKeysFromFolder(node);
              setSelectedRowKeys(prev => prev.filter(key => !allFileKeys.includes(key)));
            }
            // ファイルの選択/選択解除は通常通り処理
            else {
              setSelectedRowKeys(checkedKeys as React.Key[]);
            }
          }}
        />
      </Card>

      <Modal
        title="ファイル削除の確認"
        open={isDeleteModalVisible}
        onOk={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        okText="削除"
        okType="danger"
        cancelText="キャンセル"
      >
        <p>選択した {selectedRowKeys.length} 件のファイルを削除します。よろしいですか？</p>
      </Modal>
    </div>
  );
};

export default FilesPage;
