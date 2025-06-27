
import { vi } from 'vitest';

export const getMyOrders = vi.fn();
export const cancelOrder = vi.fn();

const orderServiceMock = {
  getMyOrders,
  cancelOrder,
};

export default orderServiceMock;
