import React, { useState } from 'react'
import { ConfigProvider, Layout, Modal, Form, message } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './App.css'
import SearchPage from './components/SearchPage'
import DetailPage from './components/DetailPage'
import FileTree from './components/FileTree'
import SVNResourceForm from './components/SVNResourceForm'
import { importSVNResource } from './services/api'

const { Sider, Content } = Layout

const App: React.FC = () => {
  const [messageApi, contextHolder] = message.useMessage()
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [form] = Form.useForm()

  const showModal = () => {
    setIsModalOpen(true)
  }

  const handleOk = () => {
    form
      .validateFields()
      .then(async (values: { svnUrl: string; username?: string; password?: string }) => {
        try {
          await importSVNResource(values.svnUrl, values.username, values.password)
          messageApi.success('SVNリソースのインポートを開始しました')
          setIsModalOpen(false)
          form.resetFields()
        } catch (error) {
          console.error('SVNリソースのインポートに失敗しました:', error)
          messageApi.error('SVNリソースのインポートに失敗しました')
          setIsModalOpen(false)
        }
      })
      .catch((info: unknown) => {
        console.log('Validate Failed:', info)
      })
  }

  const handleCancel = () => {
    setIsModalOpen(false)
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
          position: 'fixed',
          bottom: 0,
          left: 0,
          width: '350px',
          backgroundColor: 'white'
        }}>
          <button 
            className="search-button" 
            style={{ width: '100%' }}
            onClick={showModal}
          >
            Add/Update SVN Resource
          </button>
          <Modal 
            title="Add/Update SVN Resource" 
            open={isModalOpen}
            onOk={handleOk}
            onCancel={handleCancel}
          >
            <SVNResourceForm form={form} />
          </Modal>
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
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
