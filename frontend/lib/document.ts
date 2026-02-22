import api from "./api";

export async function uploadDocument(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await api.post("/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
}

export async function chatWithDocument(message: string, documentId: number | null) {
  const response = await api.post("/chat", {
    message,
    document_id: documentId,
  });
  return response.data;
}

export async function deleteDocument(documentId: number) {
  const response = await api.delete(`/upload/${documentId}`);
  return response.data;
}
