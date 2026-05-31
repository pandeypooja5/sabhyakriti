import { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, Heart, User, Search, Menu, X, LogOut, Package, Settings } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useCart } from '@/hooks/useCart';
import { useAppDispatch, useAppSelector } from '@/store/store';
import { toggleMiniCart, setMobileMenuOpen } from '@/store/slices/uiSlice';
import MiniCart from './MiniCart';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { itemCount } = useCart();
  const wishlistCount = useAppSelector((s) => s.wishlist.productIds.length);
  const miniCartOpen = useAppSelector((s) => s.ui.miniCartOpen);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchExpanded, setSearchExpanded] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close user menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/sarees?search=${encodeURIComponent(searchQuery.trim())}`);
      setSearchQuery('');
    }
  };

  const handleLogout = async () => {
    await logout();
    setUserMenuOpen(false);
    navigate('/');
  };

  return (
    <header className="sticky top-0 z-40 bg-ivory-100/95 backdrop-blur-sm border-b border-ivory-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-24 gap-4">
          {/* Logo + Brand Name */}
          <Link to="/" className="flex items-center gap-2 flex-shrink-0" data-testid="header-logo">
            <img src="/logo.png" alt="SabhyaKriti" className="h-24 w-auto hidden sm:block" />
            <img src="/logo.png" alt="SabhyaKriti" className="h-20 w-auto sm:hidden" />
            <span className="hidden sm:inline font-playfair font-bold text-xl">
              <span style={{ color: '#C9A042' }}>Sabhya</span>
              <span style={{ color: '#8B1A1A' }}>Kriti</span>
            </span>
          </Link>

          {/* Expandable Search */}
          <div ref={searchRef} className="flex-1 max-w-lg">
            {searchExpanded ? (
              <form onSubmit={handleSearch} className="w-full">
                <div className="relative w-full">
                  <input
                    type="search"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search sarees, fabrics, occasions..."
                    data-testid="header-search-input"
                    className="w-full pl-4 pr-10 py-2 text-sm border border-ivory-500 rounded-full bg-ivory-50 placeholder-brand-textMuted focus:outline-none focus:ring-2 focus:ring-gold-600/40 focus:border-gold-500"
                    autoFocus
                  />
                  <button
                    type="submit"
                    data-testid="header-search-btn"
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-brand-textMuted hover:text-gold-600"
                    aria-label="Search"
                  >
                    <Search className="h-4 w-4" />
                  </button>
                </div>
              </form>
            ) : null}
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {/* Search Icon */}
            <button
              className="p-2 text-brand-textMuted hover:text-gold-700 transition-colors"
              onClick={() => setSearchExpanded(!searchExpanded)}
              aria-label="Search"
            >
              <Search className="h-5 w-5" />
            </button>

            {/* Wishlist */}
            <Link
              to="/account/wishlist"
              className="relative p-2 text-brand-textMuted hover:text-gold-700 transition-colors"
              data-testid="wishlist-icon"
              aria-label="Wishlist"
            >
              <Heart className="h-5 w-5" />
              {wishlistCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 h-4 w-4 flex items-center justify-center bg-burgundy-500 text-white text-xs rounded-full font-bold">
                  {wishlistCount > 9 ? '9+' : wishlistCount}
                </span>
              )}
            </Link>

            {/* Cart */}
            <div className="relative">
              <button
                onClick={() => dispatch(toggleMiniCart())}
                className="relative p-2 text-brand-textMuted hover:text-gold-700 transition-colors"
                data-testid="cart-icon"
                aria-label="Shopping cart"
              >
                <ShoppingCart className="h-5 w-5" />
                {itemCount > 0 && (
                  <span className="absolute -top-0.5 -right-0.5 h-4 w-4 flex items-center justify-center bg-burgundy-500 text-white text-xs rounded-full font-bold">
                    {itemCount > 9 ? '9+' : itemCount}
                  </span>
                )}
              </button>
              {miniCartOpen && <MiniCart onClose={() => dispatch(toggleMiniCart())} />}
            </div>

            {/* User Menu */}
            <div className="relative" ref={userMenuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-1.5 p-2 text-brand-textMuted hover:text-gold-700 transition-colors"
                data-testid="user-menu-btn"
                aria-label="User menu"
              >
                {user?.avatar ? (
                  <img src={user.avatar} alt={user.name} className="h-7 w-7 rounded-full object-cover" />
                ) : (
                  <User className="h-5 w-5" />
                )}
                <span className="hidden sm:block text-sm font-medium">
                  {user?.name?.split(' ')[0] ?? 'Account'}
                </span>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-48 bg-ivory-100 rounded shadow-lg border border-ivory-400 py-2 z-50 animate-fade-in">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 border-b border-ivory-400">
                        <p className="text-sm font-semibold text-brand-text truncate">{user?.name}</p>
                        <p className="text-xs text-brand-textMuted truncate">{user?.email}</p>
                      </div>
                      <Link
                        to="/account"
                        onClick={() => setUserMenuOpen(false)}
                        data-testid="user-menu-account"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-brand-text hover:bg-ivory-200"
                      >
                        <User className="h-4 w-4" /> My Account
                      </Link>
                      <Link
                        to="/orders"
                        onClick={() => setUserMenuOpen(false)}
                        data-testid="user-menu-orders"
                        className="flex items-center gap-2 px-4 py-2 text-sm text-brand-text hover:bg-ivory-200"
                      >
                        <Package className="h-4 w-4" /> Orders
                      </Link>
                      {isAdmin && (
                        <Link
                          to="/admin"
                          onClick={() => setUserMenuOpen(false)}
                          data-testid="user-menu-admin"
                          className="flex items-center gap-2 px-4 py-2 text-sm text-gold-700 hover:bg-gold-50"
                        >
                          <Settings className="h-4 w-4" /> Admin Panel
                        </Link>
                      )}
                      <div className="border-t border-ivory-400 mt-1 pt-1">
                        <button
                          onClick={handleLogout}
                          data-testid="user-menu-logout"
                          className="flex items-center gap-2 w-full px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                        >
                          <LogOut className="h-4 w-4" /> Sign Out
                        </button>
                      </div>
                    </>
                  ) : (
                    <>
                      <Link
                        to="/login"
                        onClick={() => setUserMenuOpen(false)}
                        data-testid="user-menu-login"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                      >
                        Sign In
                      </Link>
                      <Link
                        to="/register"
                        onClick={() => setUserMenuOpen(false)}
                        data-testid="user-menu-register"
                        className="block px-4 py-2 text-sm text-saffron-500 font-medium hover:bg-saffron-50"
                      >
                        Create Account
                      </Link>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Mobile Menu Toggle */}
            <button
              className="md:hidden p-2 text-gray-600"
              data-testid="mobile-menu-toggle"
              onClick={() => dispatch(setMobileMenuOpen(true))}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
      <div className="h-px bg-gradient-to-r from-transparent via-gold-600/40 to-transparent" />
    </header>
  );
};

export default Header;
