import { useState } from 'react';
import { Link, useLocation, Outlet } from 'react-router-dom';
import {
  LayoutDashboard, Package, Tag, ShoppingBag, RotateCcw, Users,
  Ticket, Warehouse, BarChart3, Menu, X, LogOut, ChevronRight,
} from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { cn } from '@/lib/utils';

const navItems = [
  { label: 'Dashboard', href: '/admin', icon: LayoutDashboard },
  { label: 'Products', href: '/admin/products', icon: Package },
  { label: 'Categories', href: '/admin/categories', icon: Tag },
  { label: 'Orders', href: '/admin/orders', icon: ShoppingBag },
  { label: 'Returns', href: '/admin/returns', icon: RotateCcw },
  { label: 'Customers', href: '/admin/customers', icon: Users },
  { label: 'Coupons', href: '/admin/coupons', icon: Ticket },
  { label: 'Inventory', href: '/admin/inventory', icon: Warehouse },
  { label: 'Reports', href: '/admin/reports', icon: BarChart3 },
];

const AdminLayout: React.FC = () => {
  const location = useLocation();
  const { user, logout } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-teal-800 text-white flex flex-col transition-transform duration-300',
          'lg:static lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
        data-testid="admin-sidebar"
      >
        <div className="flex items-center justify-between h-16 px-4 border-b border-teal-700">
          <Link to="/admin" className="text-lg font-bold">
            Sabh<span className="text-saffron-400">yakriti</span>
            <span className="text-xs ml-1 text-teal-300">Admin</span>
          </Link>
          <button
            onClick={() => setSidebarOpen(false)}
            className="lg:hidden text-teal-300 hover:text-white"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 px-2 py-4 space-y-0.5 overflow-y-auto">
          {navItems.map(({ label, href, icon: Icon }) => {
            const isActive = location.pathname === href ||
              (href !== '/admin' && location.pathname.startsWith(href));
            return (
              <Link
                key={href}
                to={href}
                onClick={() => setSidebarOpen(false)}
                data-testid={`admin-nav-${label.toLowerCase()}`}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-teal-600 text-white'
                    : 'text-teal-100 hover:bg-teal-700 hover:text-white'
                )}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {label}
                {isActive && <ChevronRight className="h-3 w-3 ml-auto" />}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-teal-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-8 w-8 rounded-full bg-saffron-500 flex items-center justify-center text-white text-sm font-bold">
              {user?.name?.[0] ?? 'A'}
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{user?.name}</p>
              <p className="text-xs text-teal-300 truncate">{user?.role}</p>
            </div>
          </div>
          <button
            onClick={() => logout()}
            data-testid="admin-logout"
            className="flex items-center gap-2 w-full px-3 py-2 text-sm text-teal-200 hover:text-white hover:bg-teal-700 rounded-lg transition-colors"
          >
            <LogOut className="h-4 w-4" /> Sign Out
          </button>
        </div>
      </aside>

      {/* Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Admin Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-4 gap-4 flex-shrink-0">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-1.5 text-gray-600 hover:text-gray-900"
            data-testid="admin-menu-toggle"
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex-1">
            <h1 className="text-base font-semibold text-gray-900">
              {navItems.find((n) => n.href === location.pathname ||
                (n.href !== '/admin' && location.pathname.startsWith(n.href)))?.label ?? 'Admin'}
            </h1>
          </div>
          <Link
            to="/"
            className="text-sm text-saffron-500 hover:text-saffron-600 font-medium"
          >
            View Store
          </Link>
        </header>

        <main className="flex-1 overflow-y-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
