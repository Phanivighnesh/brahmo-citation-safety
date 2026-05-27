import axios from "axios";
const BASE = "http://localhost:8000/api";

export const fetchMatters  = ()      => axios.get(`${BASE}/matters`).then(r => r.data);
export const fetchHealth   = ()      => axios.get(`${BASE}/health`).then(r => r.data);
export const fetchCompare  = (query) => axios.post(`${BASE}/query/compare`, { query }).then(r => r.data);
