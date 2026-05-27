import HeroImageSection from '@/components/home/HeroImageSection';
import WorldOfSabhyaKritiSection from '@/components/home/WorldOfSabhyaKritiSection';
import FabricTypesSection from '@/components/home/FabricTypesSection';

const HomePage: React.FC = () => {
  return (
    <div data-testid="home-page">
      {/* Full-width Hero Image Section */}
      <HeroImageSection />

      {/* Full-width World of SabhyaKriti Section */}
      <WorldOfSabhyaKritiSection />

      {/* Fabric Types Section */}
      <FabricTypesSection />
    </div>
  );
};

export default HomePage;
