// src/api/ApiClient.ts
import axios, { AxiosInstance } from "axios";

export class ApiClient {
  private client: AxiosInstance;
  constructor(baseURL = "/api/v1") {
    this.client = axios.create({ baseURL, withCredentials: true });
  }
  get<T>(url: string) { return this.client.get<T>(url).then(r => r.data); }
  post<T, B>(url: string, body: B) { return this.client.post<T>(url, body).then(r => r.data); }
}

// src/services/transactionService.ts
import { ApiClient } from "../api/ApiClient";
import { TransactionRead } from "../models/Transaction";

export class TransactionService {
  constructor(private http = new ApiClient()) {}
  list() { return this.http.get<TransactionRead[]>("/transactions"); }
  create(data: Omit<TransactionRead, "tx_id"|"paid"|"paid_date">) {
    return this.http.post<TransactionRead>("/transactions", data);
  }
}

