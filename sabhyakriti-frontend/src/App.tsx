import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';

// Layouts
import AppLayout from '@/components/layout/AppLayout';
import AdminLayout from '@/components/layout/AdminLayout';

// Guards
import ProtectedRoute from '@/components/shared/ProtectedRoute';
import AdminRoute from '@/components/shared/AdminRoute';

// Home
import HomePage from '@/pages/home/HomePage';

// Auth
import LoginPage from '@/pages/auth/LoginPage';
import RegisterPage from '@/pages/auth/RegisterPage';
import VerifyEmailPage from '@/pages/auth/VerifyEmailPage';
import ForgotPasswordPage from '@/pages/auth/ForgotPasswordPage';
import ResetPasswordPage from '@/pages/auth/ResetPasswordPage';
import OAuthCallbackPage from '@/pages/auth/OAuthCallbackPage';

// Catalog
import PLPPage from '@/pages/catalog/PLPPage';

// Product
import PDPPage from '@/pages/product/PDPPage';

// Cart
import CartPage from '@/pages/cart/CartPage';

// Checkout
import CheckoutPage from '@/pages/checkout/CheckoutPage';
import OrderConfirmationPage from '@/pages/checkout/OrderConfirmationPage';

// Orders
import OrderHistoryPage from '@/pages/orders/OrderHistoryPage';
import OrderDetailPage from '@/pages/orders/OrderDetailPage';

// Account
import AccountPage from '@/pages/account/AccountPage';
import WishlistPage from '@/pages/account/WishlistPage';

// Admin
import AdminDashboard from '@/pages/admin/AdminDashboard';
import ProductManager from '@/pages/admin/products/ProductManager';
import ProductForm from '@/pages/admin/products/ProductForm';
import BulkImportPage from '@/pages/admin/products/BulkImportPage';
import CategoryManager from '@/pages/admin/categories/CategoryManager';
import AdminOrderManager from '@/pages/admin/orders/AdminOrderManager';
import AdminOrderDetail from '@/pages/admin/orders/AdminOrderDetail';
import ReturnManager from '@/pages/admin/returns/ReturnManager';
import CustomerManager from '@/pages/admin/customers/CustomerManager';
import CustomerDetail from '@/pages/admin/customers/CustomerDetail';
import CouponManager from '@/pages/admin/coupons/CouponManager';
import InventoryManager from '@/pages/admin/inventory/InventoryManager';
import SalesReport from '@/pages/admin/reports/SalesReport';

const router = createBrowserRouter([
  // Public routes with AppLayout
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <PLPPage /> },
      { path: 'sarees', element: <PLPPage /> },
      { path: 'sarees/:slug', element: <PDPPage /> },
      { path: 'cart', element: <CartPage /> },

      // Auth
      { path: 'login', element: <LoginPage /> },
      { path: 'register', element: <RegisterPage /> },
      { path: 'verify-email', element: <VerifyEmailPage /> },
      { path: 'forgot-password', element: <ForgotPasswordPage /> },
      { path: 'reset-password', element: <ResetPasswordPage /> },
      { path: 'auth/callback', element: <OAuthCallbackPage /> },

      // Protected routes
      {
        path: 'checkout',
        element: <ProtectedRoute><CheckoutPage /></ProtectedRoute>,
      },
      {
        path: 'order-confirmation/:orderId',
        element: <ProtectedRoute><OrderConfirmationPage /></ProtectedRoute>,
      },
      {
        path: 'orders',
        element: <ProtectedRoute><OrderHistoryPage /></ProtectedRoute>,
      },
      {
        path: 'orders/:orderId',
        element: <ProtectedRoute><OrderDetailPage /></ProtectedRoute>,
      },
      {
        path: 'account',
        element: <ProtectedRoute><AccountPage /></ProtectedRoute>,
      },
      {
        path: 'account/wishlist',
        element: <ProtectedRoute><WishlistPage /></ProtectedRoute>,
      },
    ],
  },

  // Admin routes with AdminLayout
  {
    path: '/admin',
    element: <AdminRoute><AdminLayout /></AdminRoute>,
    children: [
      { index: true, element: <AdminDashboard /> },

      // Products
      { path: 'products', element: <ProductManager /> },
      { path: 'products/new', element: <ProductForm /> },
      { path: 'products/:id/edit', element: <ProductForm /> },
      { path: 'products/bulk-import', element: <BulkImportPage /> },

      // Categories
      { path: 'categories', element: <CategoryManager /> },

      // Orders
      { path: 'orders', element: <AdminOrderManager /> },
      { path: 'orders/:orderId', element: <AdminOrderDetail /> },

      // Returns
      { path: 'returns', element: <ReturnManager /> },

      // Customers
      { path: 'customers', element: <CustomerManager /> },
      { path: 'customers/:id', element: <CustomerDetail /> },

      // Coupons
      { path: 'coupons', element: <CouponManager /> },

      // Inventory
      { path: 'inventory', element: <InventoryManager /> },

      // Reports
      { path: 'reports', element: <SalesReport /> },
    ],
  },

  // Catch-all
  { path: '*', element: <Navigate to="/" replace /> },
]);

const App: React.FC = () => {
  return <RouterProvider router={router} />;
};

export default App;
