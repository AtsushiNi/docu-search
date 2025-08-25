import { Form, Input } from 'antd'
import type { FormInstance } from 'antd/es/form/Form'

interface SVNResourceFormProps {
  form: FormInstance
}

const SVNResourceForm = ({ form }: SVNResourceFormProps) => {
  return (
    <Form
      form={form}
      layout="vertical"
      name="svn_resource_form"
    >
      <Form.Item
        name="svnUrl"
        label="SVN URL"
        rules={[
          {
            required: true,
            message: 'SVN URLを入力してください',
          },
        ]}
      >
        <Input placeholder="https://svn.example.com/repository/trunk" />
      </Form.Item>

      <Form.Item
        name="ipAddress"
        label="IP Address (Optional)"
      >
        <Input />
      </Form.Item>
      
      <Form.Item
        name="username"
        label="User Name"
      >
        <Input placeholder="username" />
      </Form.Item>

      <Form.Item
        name="password"
        label="Password"
      >
        <Input.Password placeholder="password" />
      </Form.Item>

      <div style={{ color: '#888', fontSize: '0.8rem', marginTop: '16px' }}>
        処理には時間がかかることがあります
      </div>
    </Form>
  )
}

export default SVNResourceForm
