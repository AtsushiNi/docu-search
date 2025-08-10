import React, { useState } from 'react'
import { ConfigProvider, Layout, Modal, Form, message } from 'antd'
import { importSVNResource } from './services/api'
import jaJP from 'antd/locale/ja_JP'
import './App.css'
import FileTree from './components/FileTree'
import SearchSection from './components/SearchSection'
import PDFViewer from './components/PDFViewer'
import SVNResourceForm from './components/SVNResourceForm'
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

  return (
    <ConfigProvider locale={jaJP} theme={{hashed: false}}>
      {contextHolder}
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={350} theme="light">
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
            <SearchSection />
            <div style={{ marginTop: '24px' }}>
              <PDFViewer filename="J5by6KGRTDw0f2vonu2T2S4A4QwVQro89OY3YIlJEH0" />
            </div>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

export default App
