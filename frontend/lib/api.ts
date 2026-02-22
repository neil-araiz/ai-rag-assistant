import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.response.use(
    response => response,
    error => {
        if (error.response) {
            console.error("API Error:", error.response.data);
            throw error.response.data;
        }
        throw error;
    }
);

export default api;