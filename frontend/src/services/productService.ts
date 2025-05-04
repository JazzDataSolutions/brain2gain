import { ProductDTO } from "../models/Product";
import { IHttpClient } from "../api/ApiClient";

export interface IProductService {
  list(): Promise<ProductDTO[]>;
  create(dto: Omit<ProductDTO, "product_id">): Promise<ProductDTO>;
}

export class ProductService implements IProductService {
  constructor(private http: IHttpClient) {}
  list()   { return this.http.get<ProductDTO[]>("/products"); }
  create(dto) { return this.http.post<ProductDTO, typeof dto>("/products", dto); }
}

