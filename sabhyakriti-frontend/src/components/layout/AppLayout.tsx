import { useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { useAppDispatch } from '@/store/store';
import { useAuth } from '@/hooks/useAuth';
import { fetchCart } from '@/store/slices/cartSlice';
import { fetchWishlist } from '@/store/slices/wishlistSlice';
import Header from './Header';
import CategoryNav from './CategoryNav';
import Footer from './Footer';

const AppLayout: React.FC = () => {
  const dispatch = useAppDispatch();
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      dispatch(fetchCart());
      dispatch(fetchWishlist());
    }
  }, [dispatch, isAuthenticated]);

  return (
    <div className="flex flex-col min-h-screen bg-[#FAFAFA]">
      <Header />
      <CategoryNav />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
};

export default AppLayout;
