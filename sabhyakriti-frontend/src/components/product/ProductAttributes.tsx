import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import type { Product } from '@/types';
import { cn } from '@/lib/utils';

interface ProductAttributesProps {
  product: Product;
}

interface AccordionItemProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

const AccordionItem: React.FC<AccordionItemProps> = ({ title, children, defaultOpen = false }) => {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-gray-100">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full py-3 text-left text-sm font-semibold text-gray-800"
        data-testid={`accordion-${title.toLowerCase().replace(/\s+/g, '-')}`}
      >
        {title}
        <ChevronDown className={cn('h-4 w-4 text-gray-400 transition-transform', open && 'rotate-180')} />
      </button>
      {open && <div className="pb-3 text-sm text-gray-600">{children}</div>}
    </div>
  );
};

const AttributeRow: React.FC<{ label: string; value: string | number | boolean | undefined }> = ({ label, value }) => {
  if (value === undefined || value === null || value === '') return null;
  const displayValue = typeof value === 'boolean' ? (value ? 'Yes' : 'No') : String(value);
  return (
    <div className="flex gap-3 py-1">
      <span className="w-36 text-gray-500 flex-shrink-0">{label}</span>
      <span className="text-gray-900 font-medium">{displayValue}</span>
    </div>
  );
};

const ProductAttributes: React.FC<ProductAttributesProps> = ({ product }) => {
  return (
    <div className="mt-4" data-testid="product-attributes">
      <AccordionItem title="Product Details" defaultOpen>
        <div className="space-y-0.5">
          <AttributeRow label="Fabric" value={product.fabric} />
          <AttributeRow label="Colour" value={product.color} />
          <AttributeRow label="Work" value={product.weaveType} />
          {product.length ? <AttributeRow label="Saree Length" value={`${product.length} meters`} /> : null}
          {product.blouseLength ? <AttributeRow label="Blouse Length" value={`${product.blouseLength} meters`} /> : null}
          <AttributeRow label="Blouse Included" value={product.blouseIncluded} />
        </div>
      </AccordionItem>

      {product.careInstructions && (
        <AccordionItem title="Care Instructions">
          <p className="leading-relaxed">{product.careInstructions}</p>
        </AccordionItem>
      )}

      <AccordionItem title="Shipping & Delivery">
        <p className="leading-relaxed">
          We offer <strong className="font-semibold text-gray-800">pan-India shipping</strong> on all orders. Your
          saree will be packed with care and dispatched within{' '}
          <strong className="font-semibold text-gray-800">2-4 business days</strong>. Delivery typically takes{' '}
          <strong className="font-semibold text-gray-800">5-7 working days</strong>, depending on your location.
          You'll receive tracking details as soon as your order is shipped.
        </p>
      </AccordionItem>

      <AccordionItem title="Return & Refund">
        <div className="space-y-3 text-sm text-gray-600">
          <p className="leading-relaxed">
            We want you to be completely satisfied with your purchase. Here's how we handle returns and refunds:
          </p>
          <ul className="space-y-2 leading-relaxed">
            <li>
              Accepted only in case of a <strong className="font-semibold text-gray-800">wrong size</strong> or{' '}
              <strong className="font-semibold text-gray-800">incorrect product delivered</strong>.
            </li>
            <li>
              Provided <strong className="font-semibold text-gray-800">only if the product is damaged</strong> upon delivery.
            </li>
            <li>
              <strong className="font-semibold text-gray-800">Unboxing video</strong> is required as proof for any return or refund request.
            </li>
            <li>
              Return request must be submitted within{' '}
              <strong className="font-semibold text-gray-800">24 Hours</strong> after receiving the order.
            </li>
          </ul>
          <p className="leading-relaxed pt-1">
            For assistance, please contact our support team with your order ID and issue details.
          </p>
        </div>
      </AccordionItem>
    </div>
  );
};

export default ProductAttributes;
