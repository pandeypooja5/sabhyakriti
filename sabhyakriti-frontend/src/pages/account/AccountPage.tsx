import { useState } from 'react';
import { User, MapPin, Heart, Package } from 'lucide-react';
import ProfileForm from '@/components/account/ProfileForm';
import AddressBook from '@/components/account/AddressBook';
import WishlistPage from './WishlistPage';
import OrderHistoryPage from '@/pages/orders/OrderHistoryPage';
import { cn } from '@/lib/utils';

const tabs = [
  { id: 'profile', label: 'Profile', Icon: User },
  { id: 'addresses', label: 'Addresses', Icon: MapPin },
  { id: 'wishlist', label: 'Wishlist', Icon: Heart },
  { id: 'orders', label: 'Orders', Icon: Package },
] as const;

type TabId = typeof tabs[number]['id'];

const AccountPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabId>('profile');

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6" data-testid="account-page">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">My Account</h1>

      {/* Tab Bar */}
      <div className="flex gap-1 bg-gray-100 p-1 rounded-xl mb-6 overflow-x-auto">
        {tabs.map(({ id, label, Icon }) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            data-testid={`account-tab-${id}`}
            className={cn(
              'flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors',
              activeTab === id ? 'bg-white text-saffron-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'profile' && <ProfileForm />}
        {activeTab === 'addresses' && <AddressBook />}
        {activeTab === 'wishlist' && <WishlistPage />}
        {activeTab === 'orders' && <OrderHistoryPage />}
      </div>
    </div>
  );
};

export default AccountPage;
