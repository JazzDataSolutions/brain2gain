// src/models/User.ts
export interface UserRead {
  user_id: number;
  username: string;
  email: string;
  is_active: boolean;
  roles: string[];
}

// src/models/Transaction.ts
export interface TransactionRead {
  tx_id: number;
  type: string;
  amount: number;
  description?: string;
  customer_id?: number;
  product_id?: number;
  due_date?: string;
  paid: boolean;
  paid_date?: string;
}

// src/models/Stock.ts
export interface StockRead {
  product_id: number;
  quantity: number;
}

