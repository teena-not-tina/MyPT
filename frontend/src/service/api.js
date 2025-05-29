import axios from 'axios';

const API_URL = "http://localhost:8000/api";

export const analyzeImage = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const response = await axios.post(`${API_URL}/analyze`, formData);
  return response.data;
};
