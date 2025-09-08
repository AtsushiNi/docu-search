import React, { useState, useRef } from 'react';
import { Button, Progress, message, Typography, Input, Form } from 'antd';
import { UploadOutlined, FolderOpenOutlined } from '@ant-design/icons';
import { uploadLocalFolder } from '../services/api';

const { Text } = Typography;

interface UploadProgress {
  totalFiles: number;
  uploadedFiles: number;
  currentFile: string;
  percentage: number;
}

interface LocalFolderUploadProps {
  onUploadComplete?: () => void;
  onCancel?: () => void;
}

const LocalFolderUpload: React.FC<LocalFolderUploadProps> = ({ 
  onUploadComplete, 
  onCancel
}) => {
  const [absolutePath, setAbsolutePath] = useState('');
  const [selectedFolderInfo, setSelectedFolderInfo] = useState<{name: string, fileCount: number} | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadProgress | null>(null);
  const isCancelledRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [form] = Form.useForm();

  const handleCancel = () => {
    if (isUploading) {
      isCancelledRef.current = true;
      message.info('アップロードをキャンセル中...');
    } else {
      onCancel?.();
    }
  };

  const handleFolderSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    // フォルダ名から自動的にパスを推測
    const folderName = files[0]?.webkitRelativePath?.split('/')[0] || '選択したフォルダ';
    
    // 選択されたフォルダ情報を設定
    setSelectedFolderInfo({
      name: folderName,
      fileCount: files.length
    });
    
    // 絶対パスが入力されていない場合は、フォルダ名をヒントとして設定
    if (!absolutePath.trim()) {
      setAbsolutePath(`/path/to/${folderName}`);
      message.info(`フォルダ「${folderName}」を選択しました。絶対パスを確認・修正してアップロードを開始してください`);
      return;
    }

    setIsUploading(true);
    isCancelledRef.current = false; // キャンセルフラグをリセット
    setUploadProgress({
      totalFiles: files.length,
      uploadedFiles: 0,
      currentFile: '',
      percentage: 0
    });

    try {
      // すべてのファイルと相対パスを収集
      const fileArray: File[] = [];
      const absolutePaths: string[] = [];
      
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const webkitRelativePath = (file as { webkitRelativePath?: string }).webkitRelativePath || file.name;
        
        fileArray.push(file);
        // 各ファイルの絶対パスを生成（ベースパス + 相対パス）
        // webkitRelativePathから最初のディレクトリ部分（フォルダ名）を取り除いて結合
        const relativePathParts = webkitRelativePath.split('/');
        let adjustedRelativePath = webkitRelativePath;
        
        // 最初の部分がフォルダ名で、2つ以上の部分がある場合のみ処理
        if (relativePathParts.length > 1) {
          adjustedRelativePath = relativePathParts.slice(1).join('/');
        }
        
        absolutePaths.push(`${absolutePath}/${adjustedRelativePath}`);
      }

      // 親ジョブIDを生成
      const parentJobId = `local_upload_${Date.now()}`;
      
      // 10ファイルずつのバッチに分割してアップロード
      const BATCH_SIZE = 10;
      let uploadedCount = 0;
      const totalBatches = Math.ceil(fileArray.length / BATCH_SIZE);

      for (let i = 0; i < fileArray.length; i += BATCH_SIZE) {
        // キャンセルチェック
        if (isCancelledRef.current) {
          message.info('アップロードがキャンセルされました');
          break;
        }

        const batchIndex = Math.floor(i / BATCH_SIZE) + 1;
        const batchFiles = fileArray.slice(i, i + BATCH_SIZE);
        const batchPaths = absolutePaths.slice(i, i + BATCH_SIZE);
        
        // 現在のバッチのファイル名を表示
        const currentBatchFiles = batchFiles.map(file => 
          (file as { webkitRelativePath?: string }).webkitRelativePath || file.name
        );
        
        setUploadProgress({
          totalFiles: files.length,
          uploadedFiles: uploadedCount,
          currentFile: `バッチ ${batchIndex}/${totalBatches}: ${currentBatchFiles[0]}...`,
          percentage: Math.round((uploadedCount / files.length) * 100)
        });

        try {
          await uploadLocalFolder(batchFiles, batchPaths, parentJobId);
          uploadedCount += batchFiles.length;
          
          setUploadProgress({
            totalFiles: files.length,
            uploadedFiles: uploadedCount,
            currentFile: `${uploadedCount}/${files.length} ファイル完了`,
            percentage: Math.round((uploadedCount / files.length) * 100)
          });
        } catch (batchError) {
          console.error(`バッチ ${Math.floor(i/BATCH_SIZE) + 1} のアップロードエラー:`, batchError);
          message.error(`バッチ ${Math.floor(i/BATCH_SIZE) + 1} のアップロードに失敗しました`);
          // 次のバッチに進む
          uploadedCount += batchFiles.length;
        }

        // 少し待機してサーバー負荷を軽減
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      if (!isCancelledRef.current) {
        setUploadProgress({
          totalFiles: files.length,
          uploadedFiles: files.length,
          currentFile: '完了',
          percentage: 100
        });

        message.success('ファイルのアップロードが完了しました');
        onUploadComplete?.();
      } else {
        message.info(`アップロードがキャンセルされました (${uploadedCount}/${files.length} ファイル完了)`);
      }
    } catch (error) {
      console.error('アップロードエラー:', error);
      message.error('アップロード中にエラーが発生しました');
    } finally {
      setIsUploading(false);
      setUploadProgress(null);
      setAbsolutePath('');
      setSelectedFolderInfo(null);
      form.resetFields();
      
      // ファイル入力をリセットして同じフォルダを再度選択できるようにする
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };


  return (
    <div style={{ textAlign: 'center', padding: '20px' }}>
      <input
        ref={fileInputRef}
        type="file"
        // @ts-expect-error - webkitdirectoryは標準ではないが主要ブラウザでサポート
        webkitdirectory=""
        multiple
        style={{ display: 'none' }}
        onChange={handleFolderSelect}
        accept="*/*"
      />
      
      {!isUploading ? (
        <>
          <FolderOpenOutlined style={{ fontSize: '48px', color: '#1890ff', marginBottom: '16px' }} />
          <Text style={{ display: 'block', marginBottom: '16px' }}>
            アップロードするローカルフォルダを選択してください
          </Text>
          
          <Button 
            type="primary" 
            icon={<UploadOutlined />}
            size="large"
            onClick={() => fileInputRef.current?.click()}
            style={{ marginBottom: '16px' }}
          >
            フォルダを選択
          </Button>
          
          {selectedFolderInfo && (
            <div style={{ 
              backgroundColor: '#f5f5f5', 
              padding: '12px', 
              borderRadius: '6px', 
              marginBottom: '16px',
              textAlign: 'left'
            }}>
              <Text strong style={{ display: 'block', marginBottom: '4px' }}>
                選択されたフォルダ情報
              </Text>
              <Text type="secondary" style={{ display: 'block', fontSize: '14px' }}>
                フォルダ名: {selectedFolderInfo.name}
              </Text>
              <Text type="secondary" style={{ display: 'block', fontSize: '14px' }}>
                ファイル数: {selectedFolderInfo.fileCount} ファイル
              </Text>
            </div>
          )}
          
          <Form
            form={form}
            layout="vertical"
            style={{ marginBottom: '24px' }}
            onValuesChange={(changedValues) => {
              if (changedValues.absolutePath !== undefined) {
                setAbsolutePath(changedValues.absolutePath);
              }
            }}
          >
            <Form.Item
              name="absolutePath"
              label="フォルダの絶対パス"
              rules={[
                { required: true, message: '絶対パスを入力してください' },
                { pattern: /^\/.*/, message: '絶対パスはスラッシュ(/)で始まる必要があります' }
              ]}
            >
              <Input 
                placeholder="/Users/username/documents/folder" 
                value={absolutePath}
                onChange={(e) => setAbsolutePath(e.target.value)}
              />
            </Form.Item>
          </Form>
          
          {absolutePath.trim() && (
            <Button 
              type="primary" 
              icon={<UploadOutlined />}
              size="large"
              onClick={() => {
                if (fileInputRef.current?.files && fileInputRef.current.files.length > 0) {
                  // ファイルが選択されている場合はアップロードを開始
                  handleFolderSelect({ target: { files: fileInputRef.current.files } } as React.ChangeEvent<HTMLInputElement>);
                } else {
                  message.info('まずフォルダを選択してください');
                }
              }}
            >
              アップロード開始
            </Button>
          )}
        </>
      ) : (
        <>
          <Text strong style={{ display: 'block', marginBottom: '16px' }}>
            アップロード中...
          </Text>
          {uploadProgress && (
            <>
              <Progress 
                percent={uploadProgress.percentage} 
                status="active"
                style={{ marginBottom: '16px' }}
              />
              <Text type="secondary" style={{ display: 'block', marginBottom: '8px' }}>
                {uploadProgress.uploadedFiles} / {uploadProgress.totalFiles} ファイル
              </Text>
              {uploadProgress.currentFile && (
                <Text type="secondary" style={{ display: 'block', fontSize: '12px' }}>
                  現在: {uploadProgress.currentFile}
                </Text>
              )}
            </>
          )}
          <Button 
            onClick={handleCancel}
            disabled={!isUploading}
            style={{ marginTop: '16px' }}
          >
            キャンセル
          </Button>
        </>
      )}
    </div>
  );
};

export default LocalFolderUpload;
