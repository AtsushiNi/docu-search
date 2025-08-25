import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundaryでエラーをキャッチ:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ 
          padding: '20px', 
          textAlign: 'center', 
          color: 'red',
          border: '1px solid #ffcccc',
          backgroundColor: '#fff0f0',
          borderRadius: '4px',
          margin: '10px'
        }}>
          <h3>エラーが発生しました</h3>
          <p>ページの表示中に問題が発生しました。</p>
          <details style={{ textAlign: 'left', marginTop: '10px' }}>
            <summary>エラーの詳細</summary>
            <pre style={{ 
              whiteSpace: 'pre-wrap', 
              fontSize: '12px',
              backgroundColor: '#f8f8f8',
              padding: '10px',
              borderRadius: '4px',
              overflow: 'auto'
            }}>
              {this.state.error?.toString()}
            </pre>
          </details>
          <button 
            onClick={() => this.setState({ hasError: false, error: undefined })}
            style={{
              marginTop: '10px',
              padding: '8px 16px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            再読み込み
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
