import React, { useState } from 'react'
import { ConfigProvider, Layout, Modal, Form, message, Dropdown } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import SearchPage from './components/SearchPage'
import DetailPage from './components/DetailPage'
import JobsPage from './components/JobsPage'
import FileTree from './components/FileTree'
import SVNResourceForm from './components/SVNResourceForm'
import LocalFolderUpload from './components/LocalFolderUpload'
import { importSVNResource } from './services/api'

const { Sider, Content } = Layout

const App: React.FC = () => {
  const [messageApi, contextHolder] = message.useMessage()
  const [isSVNModalOpen, setIsSVNModalOpen] = useState(false)
  const [isLocalFolderModalOpen, setIsLocalFolderModalOpen] = useState(false)
  const [form] = Form.useForm()

  const showSVNModal = () => {
    setIsSVNModalOpen(true)
  }

  const showLocalFolderModal = () => {
    setIsLocalFolderModalOpen(true)
  }

  const handleSVNOk = () => {
    form
      .validateFields()
      .then(async (values: { svnUrl: string; username?: string; password?: string; ipAddress?: string }) => {
        try {
          await importSVNResource(values.svnUrl, values.username, values.password, values.ipAddress)
          messageApi.success('SVNリソースのインポートを開始しました')
          setIsSVNModalOpen(false)
          form.resetFields()
        } catch (error) {
          console.error('SVNリソースのインポートに失敗しました:', error)
          messageApi.error('SVNリソースのインポートに失敗しました')
          setIsSVNModalOpen(false)
        }
      })
      .catch((info: unknown) => {
        console.log('Validate Failed:', info)
      })
  }

  const handleSVNCancel = () => {
    setIsSVNModalOpen(false)
  }

  const handleLocalFolderCancel = () => {
    setIsLocalFolderModalOpen(false)
  }

  const AppLayout = ({ children }: { children: React.ReactNode }) => (
    <Layout style={{ minHeight: '100vh' }}>
      {contextHolder}
      <Sider width={350} theme="light">
        <a href="/" style={{ 
          display: 'block', 
          padding: '16px', 
          paddingBottom: 0,
          textAlign: 'center',
          fontSize: '1.5rem',
          fontWeight: 'bold',
          color: '#1890ff',
          textDecoration: 'none',
          transition: 'color 0.3s'
        }}>
          Docu Search
        </a>
        <FileTree />
        <div style={{ 
          padding: '16px', 
          borderTop: '1px solid #eee',
          borderRadius: '4px',
          position: 'fixed',
          bottom: 80,
          left: 0,
          width: '350px',
          backgroundColor: 'white'
        }}>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'svn',
                  label: 'SVNリソース',
                  onClick: showSVNModal
                },
                {
                  key: 'local',
                  label: 'ローカルフォルダ',
                  onClick: showLocalFolderModal
                }
              ]
            }}
            trigger={['click']}
          >
            <button 
              className="search-button" 
              style={{ width: '100%' }}
            >
              リソースの追加
            </button>
          </Dropdown>
          <Modal 
            title="SVNリソースの追加/更新" 
            open={isSVNModalOpen}
            onOk={handleSVNOk}
            onCancel={handleSVNCancel}
          >
            <SVNResourceForm form={form} />
          </Modal>
          <Modal 
            title="ローカルフォルダからアップロード" 
            open={isLocalFolderModalOpen}
            onCancel={handleLocalFolderCancel}
            footer={null}
            width={600}
          >
            <LocalFolderUpload 
              onUploadComplete={() => {
                messageApi.success('ローカルフォルダのアップロードが完了しました');
                setIsLocalFolderModalOpen(false);
                // 必要に応じてファイルツリーの更新などを実装
              }}
              onCancel={handleLocalFolderCancel}
            />
          </Modal>
        </div>
        <div style={{
          marginBottom: '16px',
          padding: '16px',
          backgroundColor: 'white',
          borderRadius: '4px',
          width: '350px',
          position: 'fixed',
          bottom: 0,
          left: 0,
        }}>
          <button 
            style={{ width: '100%', backgroundColor: '#f0f0f0', borderRadius: 4 }}
            onClick={() => window.location.href = '/jobs'}
          >
            ジョブ管理
          </button>
        </div>
      </Sider>
      <Layout style={{ width: "calc(100vw - 350px)" }}>
        <Content style={{ padding: '24px' }}>
          {children}
        </Content>
      </Layout>
    </Layout>
  )

  return (
    <ConfigProvider locale={jaJP} theme={{hashed: false}}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={
            <AppLayout>
              <SearchPage />
            </AppLayout>
          } />
          <Route path="/documents/:id" element={
            <AppLayout>
              <DetailPage />
            </AppLayout>
          } />
          <Route path="/jobs" element={
            <AppLayout>
              <JobsPage />
            </AppLayout>
          } />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
