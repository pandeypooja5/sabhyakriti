import HeroBanner from './HeroBanner';
import CategoryShortcuts from './CategoryShortcuts';
import FeaturedProducts from './FeaturedProducts';
import NewArrivals from './NewArrivals';

const HomePage: React.FC = () => {
  return (
    <div data-testid="home-page">
      <HeroBanner />
      <CategoryShortcuts />
      <FeaturedProducts />
      <NewArrivals />
    </div>
  );
};

export default HomePage;
