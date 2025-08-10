import { ConfigProvider, Layout } from 'antd'
import jaJP from 'antd/locale/ja_JP'
import './App.css'
import FileTree from './components/FileTree'
import SearchSection from './components/SearchSection'
import PDFViewer from './components/PDFViewer'
const { Sider, Content } = Layout

function App() {
  return (
    <ConfigProvider locale={jaJP} theme={{hashed: false}}>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider width={350} theme="light">
          <FileTree />
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
