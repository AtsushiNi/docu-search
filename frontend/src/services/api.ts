import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

export const searchDocuments = async (query: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/search`, {
      params: { query }
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

export const exploreSVNRepo = async (repoUrl: string, path: string = '') => {
  try {
    const response = await axios.get(`${API_BASE_URL}/svn/explore`, {
      params: { repo_url: repoUrl, path }
    });
    return response.data;
  } catch (error) {
    console.error('Error exploring SVN repo:', error);
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

export const importSVNResource = async (repoUrl: string, username?: string, password?: string) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/svn/import`, {
      url: repoUrl,
      username,
      password
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

export const getDocumentMetadata = async (documentId: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/files/${documentId}`);
    const document = response.data;
    
    // 実際に保存されている項目のみを返す
    return {
      id: documentId,
      title: document.name,
      updated_at: document.updated_at,
      url: document.url,
      pdf_name: document.pdf_name || null
    };
  } catch (error) {
    console.error('Error getting document metadata:', error);
    throw error;
  }
};
