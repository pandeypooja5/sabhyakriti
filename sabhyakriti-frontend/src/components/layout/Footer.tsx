import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Instagram, Facebook, Twitter, Youtube, Mail, Phone, MapPin } from 'lucide-react';
import toast from 'react-hot-toast';

const Footer: React.FC = () => {
  const [email, setEmail] = useState('');

  const handleNewsletter = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    toast.success('Thank you for subscribing!');
    setEmail('');
  };

  return (
    <footer className="bg-[#1C110A] text-ivory-400 mt-auto" data-testid="footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <img src="/logo.png" alt="SabhyaKriti" className="h-16 w-auto brightness-90 mb-4" />
            <p className="text-sm text-ivory-400 mb-4 leading-relaxed">
              Celebrating India's rich textile heritage. Every saree tells a story of craftsmanship and tradition.
            </p>
            <div className="flex gap-3">
              {[
                { Icon: Instagram, href: '#', label: 'Instagram' },
                { Icon: Facebook, href: '#', label: 'Facebook' },
                { Icon: Twitter, href: '#', label: 'Twitter' },
                { Icon: Youtube, href: '#', label: 'YouTube' },
              ].map(({ Icon, href, label }) => (
                <a
                  key={label}
                  href={href}
                  aria-label={label}
                  data-testid={`footer-social-${label.toLowerCase()}`}
                  className="h-8 w-8 flex items-center justify-center rounded-full bg-ivory-200 text-[#1C110A] hover:border hover:border-gold-600 transition-colors"
                >
                  <Icon className="h-4 w-4" />
                </a>
              ))}
            </div>
          </div>

          {/* Quick Links */}
          <div>
            <h3 className="font-semibold mb-4 text-xs uppercase tracking-widest text-gold-500">Shop</h3>
            <ul className="space-y-2 text-sm text-ivory-400">
              {[
                { label: 'All Sarees', href: '/sarees' },
                { label: 'New Arrivals', href: '/sarees?sort=newest' },
                { label: 'Best Sellers', href: '/sarees?sort=popularity' },
                { label: 'Wedding Collection', href: '/sarees?occasion=wedding' },
                { label: 'Silk Sarees', href: '/sarees?fabric=silk' },
              ].map((link) => (
                <li key={link.label}>
                  <Link to={link.href} className="hover:text-ivory-100 font-light transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Help */}
          <div>
            <h3 className="font-semibold mb-4 text-xs uppercase tracking-widest text-gold-500">Help</h3>
            <ul className="space-y-2 text-sm text-ivory-400">
              {[
                { label: 'My Orders', href: '/orders' },
                { label: 'Track Order', href: '/orders' },
                { label: 'Returns & Exchanges', href: '/returns' },
                { label: 'Size Guide', href: '/size-guide' },
                { label: 'Contact Us', href: '/contact' },
                { label: 'FAQ', href: '/faq' },
              ].map((link) => (
                <li key={link.label}>
                  <Link to={link.href} className="hover:text-ivory-100 font-light transition-colors">
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Newsletter & Contact */}
          <div>
            <h3 className="font-semibold mb-4 text-xs uppercase tracking-widest text-gold-500">Stay Connected</h3>
            <form onSubmit={handleNewsletter} className="mb-4">
              <p className="text-sm text-ivory-400 mb-2">Get exclusive offers in your inbox.</p>
              <div className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Your email"
                  data-testid="newsletter-input"
                  className="flex-1 px-3 py-1.5 text-sm bg-ivory-200 rounded border border-ivory-400 text-brand-text placeholder-brand-textMuted focus:outline-none focus:border-gold-500"
                />
                <button
                  type="submit"
                  data-testid="newsletter-submit"
                  className="px-3 py-1.5 bg-gold-600 hover:bg-gold-700 text-white rounded text-sm transition-colors font-medium"
                >
                  Go
                </button>
              </div>
            </form>
            <ul className="space-y-2 text-sm text-ivory-400">
              <li className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-gold-600 flex-shrink-0" />
                <span>support@sabhyakriti.com</span>
              </li>
              <li className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-gold-600 flex-shrink-0" />
                <span>9160660011</span>
              </li>
              <li className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-gold-600 flex-shrink-0 mt-0.5" />
                <span>Hyderabad, Telangana, India</span>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-ivory-700 mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-gold-500">
          <p>&copy; {new Date().getFullYear()} Sabhyakriti. All rights reserved.</p>
          <div className="flex gap-4">
            <Link to="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link>
            <Link to="/terms" className="hover:text-white transition-colors">Terms of Service</Link>
            <Link to="/shipping" className="hover:text-white transition-colors">Shipping Policy</Link>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
