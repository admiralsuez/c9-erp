import { z } from 'zod';

export const loginSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
  password: z
    .string()
    .min(1, 'Password is required')
    .min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean().default(false),
});

export type LoginFormData = z.infer<typeof loginSchema>;

export const createItemSchema = z.object({
  name: z.string().min(1, 'Item name is required').min(3, 'Name must be at least 3 characters'),
  sku: z.string().min(1, 'SKU is required'),
  barcode: z.string().optional(),
  category_id: z.number().optional(),
  item_type: z.enum(['consumable', 'returnable']),
  minimum_quantity: z.number().min(0, 'Minimum quantity must be positive'),
  opening_quantity: z.number().min(0, 'Opening stock must be 0 or greater').optional(),
  description: z.string().optional(),
});

export type CreateItemFormData = z.infer<typeof createItemSchema>;

export const createVendorSchema = z.object({
  name: z.string().min(1, 'Vendor name is required').min(3, 'Name must be at least 3 characters'),
  vendor_type: z.string().optional(),
  contact_person: z.string().optional(),
  phone: z.string().optional(),
  email: z.string().email('Invalid email').optional().or(z.literal('')),
  address: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  gst: z.string().optional(),
  notes: z.string().optional(),
});

export type CreateVendorFormData = z.infer<typeof createVendorSchema>;
