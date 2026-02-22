import api from "./api";

export async function sampleApi() {
    const response = await api.get("/sample/docs-count");
    return response.data;
}