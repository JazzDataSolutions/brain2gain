import axios, { AxiosInstance } from "axios";

export interface IHttpClient {
  get<T>(url: string): Promise<T>;
  post<T, B = void>(url: string, body?: B): Promise<T>;
}

export class ApiClient implements IHttpClient {
  private client: AxiosInstance;
  constructor(baseURL = "/api/v1") {
    this.client = axios.create({ baseURL, withCredentials: true });
  }
  async get<T>(url: string)     { return (await this.client.get<T>(url)).data; }
  async post<T, B>(url: string, body?: B) { return (await this.client.post<T>(url, body)).data; }
}

