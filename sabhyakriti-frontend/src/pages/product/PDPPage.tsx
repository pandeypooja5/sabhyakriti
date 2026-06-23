import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import type { Product } from '@/types';
import { getProductBySlug } from '@/services/productService';
import ImageGallery from '@/components/product/ImageGallery';
import ProductInfo from '@/components/product/ProductInfo';
import ProductAttributes from '@/components/product/ProductAttributes';
import AddToCartSection from '@/components/product/AddToCartSection';
import ReviewSection from '@/components/product/ReviewSection';
import RelatedProducts from '@/components/product/RelatedProducts';
import SizeGuide from '@/components/product/SizeGuide';
import Breadcrumb from '@/components/shared/Breadcrumb';
import LoadingSpinner from '@/components/shared/LoadingSpinner';

const PDPPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (!slug) return;
    setLoading(true);
    setNotFound(false);
    getProductBySlug(slug)
      .then(setProduct)
      .catch((err) => {
        if (err.response?.status === 404) setNotFound(true);
        else setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) return <div className="flex justify-center items-center min-h-[60vh]"><LoadingSpinner size="lg" /></div>;

  if (notFound || !product) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-20 text-center" data-testid="pdp-not-found">
        <h2 className="text-2xl font-bold text-gray-700 mb-4">Product Not Found</h2>
        <p className="text-gray-500 mb-6">The saree you're looking for doesn't exist or may have been removed.</p>
        <button onClick={() => navigate('/sarees')} className="btn-primary">
          Browse All Sarees
        </button>
      </div>
    );
  }

  const breadcrumbs = [
    { label: 'Sarees', href: '/sarees' },
    { label: product.fabricCategories[0]?.name ?? 'Saree', href: `/sarees?fabric=${product.fabricCategories[0]?.slug}` },
    { label: product.name },
  ];

  const productUrl = `https://www.sabhyakriti.com/sarees/${product.slug}`;
  const productImage = product.images?.[0]?.url ?? 'https://www.sabhyakriti.com/hero-sarees.png';
  const fabricName = product.fabricCategories?.[0]?.name ?? 'Handcrafted';
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: product.description ?? `${fabricName} saree from Sabhyakriti. Premium handcrafted Indian saree with pan-India shipping.`,
    image: productImage,
    url: productUrl,
    brand: { '@type': 'Brand', name: 'Sabhyakriti' },
    offers: {
      '@type': 'Offer',
      priceCurrency: 'INR',
      price: product.price,
      availability: product.stockQuantity > 0 ? 'https://schema.org/InStock' : 'https://schema.org/OutOfStock',
      url: productUrl,
      seller: { '@type': 'Organization', name: 'Sabhyakriti' },
    },
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6" data-testid="pdp-page">
      <Helmet>
        <title>{`${product.name} — Buy ${fabricName} Saree Online | Sabhyakriti`}</title>
        <meta name="description" content={`Buy ${product.name} online at Sabhyakriti. ${fabricName} saree handcrafted with care. Pan-India shipping, 5-7 working days delivery.`} />
        <link rel="canonical" href={productUrl} />
        <meta property="og:title" content={`${product.name} | Sabhyakriti`} />
        <meta property="og:description" content={`${fabricName} saree — ${product.name}. Shop handcrafted sarees at Sabhyakriti.`} />
        <meta property="og:image" content={productImage} />
        <meta property="og:url" content={productUrl} />
        <meta property="og:type" content="product" />
        <meta property="product:price:amount" content={String(product.price)} />
        <meta property="product:price:currency" content="INR" />
        <script type="application/ld+json">{JSON.stringify(jsonLd)}</script>
      </Helmet>

      <Breadcrumb items={breadcrumbs} />

      <div className="mt-6 grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
        {/* Left: Images */}
        <div>
          <ImageGallery images={product.images} productName={product.name} />
        </div>

        {/* Right: Info */}
        <div>
          <ProductInfo product={product} />
          <div className="mt-6">
            <AddToCartSection product={product} />
          </div>
          <ProductAttributes product={product} />
        </div>
      </div>

      <ReviewSection
        productId={product.id}
        avgRating={product.avgRating}
        reviewCount={product.reviewCount}
      />

      <RelatedProducts productId={product.id} />

      <SizeGuide />
    </div>
  );
};

export default PDPPage;
