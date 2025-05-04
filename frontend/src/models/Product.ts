export interface ProductDTO {
  product_id: number;
  sku: string;
  name: string;
  unit_price: number;
}

/** Opcional clase con métodos de dominio */
export class Product implements ProductDTO {
  constructor(
    public product_id: number,
    public sku: string,
    public name: string,
    public unit_price: number
  ) {}

  get formattedPrice() {
    return `$${this.unit_price.toFixed(2)}`;
  }
}

