import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const searchDocuments = async (query: string, searchType: string = 'exact') => {
  try {
    const response = await axios.get(`${API_BASE_URL}/search`, {
      params: { query, search_type: searchType }
    });
    return response.data.results;
  } catch (error) {
    console.error('Error searching documents:', error);
    throw error;
  }
};

export const getFileList = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/files`);
    return response.data.files;
  } catch (error) {
    console.error('Error getting files:', error);
    throw error;
  }
};

export const getPDF = async (filename: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/pdf/${filename}`, {
      responseType: 'blob'
    });
    return response.data;
  } catch (error) {
    console.error('Error getting PDF:', error);
    throw error;
  }
};

export const importSVNResource = async (repoUrl: string, username?: string, password?: string, ipAddress?: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/svn/import`, {
      url: repoUrl,
      username,
      password,
      ip_address: ipAddress
    }, {
      headers: {
        'Content-Type': 'application/json'
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error importing SVN resource:', error);
    throw error;
  }
};

export const getDocument = async (documentId: string, includeContent: boolean = false) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/documents/${documentId}`, {
      params: { include_content: includeContent }
    });
    const document = response.data;
    
    return {
      id: documentId,
      title: document.name,
      updated_at: document.updated_at,
      url: document.url,
      pdf_name: document.pdf_name || null,
      content: includeContent ? document.content : undefined
    };
  } catch (error) {
    console.error('Error getting document:', error);
    throw error;
  }
};

export const getJobList = async (queueName?: string, status?: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/jobs`, {
      params: { queue_name: queueName, status }
    });
    return response.data;
  } catch (error) {
    console.error('Error getting job list:', error);
    throw error;
  }
};

export const getQueueStats = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/jobs/queue/stats`);
    return response.data;
  } catch (error) {
    console.error('Error getting queue stats:', error);
    throw error;
  }
};

export const uploadLocalFolder = async (files: File[], absolutePaths: string[], parentJobId: string) => {
  try {
    const formData = new FormData();
    
    // 各ファイルをFormDataに追加
    files.forEach((file, index) => {
      formData.append('files', file);
      formData.append('absolute_paths', absolutePaths[index]);
    });
    
    formData.append('parent_job_id', parentJobId);

    const response = await axios.post(`${API_BASE_URL}/upload/local-folder`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        // 進捗状況の処理（必要に応じて実装）
        if (progressEvent.total) {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      }
    });
    
    return response.data;
  } catch (error) {
    console.error('Error uploading local folder:', error);
    throw error;
  }
};
