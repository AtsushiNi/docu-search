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
    return response.data.urls;
  } catch (error) {
    console.error('Error getting file list:', error);
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
