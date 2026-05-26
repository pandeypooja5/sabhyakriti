import { Check, Package, Truck, MapPin, ShoppingBag, XCircle } from 'lucide-react';
import type { OrderStatus, OrderStatusHistory } from '@/types';
import { formatDateTime } from '@/utils/date';
import { cn } from '@/lib/utils';

interface OrderStatusTimelineProps {
  currentStatus: OrderStatus;
  history: OrderStatusHistory[];
}

const activeSteps: { status: OrderStatus; label: string; Icon: React.FC<{ className?: string }> }[] = [
  { status: 'PENDING', label: 'Order Placed', Icon: ShoppingBag },
  { status: 'CONFIRMED', label: 'Confirmed', Icon: Check },
  { status: 'PROCESSING', label: 'Processing', Icon: Package },
  { status: 'SHIPPED', label: 'Shipped', Icon: Truck },
  { status: 'DELIVERED', label: 'Delivered', Icon: MapPin },
];

const statusOrder: OrderStatus[] = ['PENDING', 'CONFIRMED', 'PROCESSING', 'SHIPPED', 'OUT_FOR_DELIVERY', 'DELIVERED'];

const OrderStatusTimeline: React.FC<OrderStatusTimelineProps> = ({ currentStatus, history }) => {
  const isCancelled = ['CANCELLED', 'RETURN_REQUESTED', 'RETURNED', 'REFUNDED'].includes(currentStatus);
  const currentIdx = statusOrder.indexOf(currentStatus);

  const getTimestamp = (status: OrderStatus) => {
    const entry = history.find((h) => h.status === status);
    return entry ? formatDateTime(entry.timestamp) : null;
  };

  return (
    <div data-testid="order-status-timeline" className="py-4">
      {isCancelled ? (
        <div className="flex items-center gap-3 p-4 bg-red-50 rounded-xl">
          <XCircle className="h-6 w-6 text-red-500 flex-shrink-0" />
          <div>
            <p className="font-semibold text-red-700">Order {currentStatus.replace('_', ' ')}</p>
            <p className="text-sm text-red-500">
              {getTimestamp(currentStatus)}
            </p>
          </div>
        </div>
      ) : (
        <div className="relative">
          {activeSteps.map(({ status, label, Icon }, idx) => {
            const stepIdx = statusOrder.indexOf(status);
            const isDone = stepIdx < currentIdx;
            const isActive = status === currentStatus;
            const timestamp = getTimestamp(status);

            return (
              <div key={status} className="flex gap-4 pb-6 last:pb-0" data-testid={`timeline-step-${status.toLowerCase()}`}>
                {/* Line */}
                <div className="flex flex-col items-center">
                  <div
                    className={cn(
                      'h-8 w-8 rounded-full flex items-center justify-center z-10 flex-shrink-0',
                      isDone ? 'bg-green-500 text-white' :
                      isActive ? 'bg-saffron-500 text-white ring-4 ring-saffron-100' :
                      'bg-gray-100 text-gray-400'
                    )}
                  >
                    <Icon className="h-4 w-4" />
                  </div>
                  {idx < activeSteps.length - 1 && (
                    <div className={cn('w-0.5 flex-1 mt-1', isDone ? 'bg-green-400' : 'bg-gray-200')} />
                  )}
                </div>
                <div className="pt-1 pb-2">
                  <p className={cn('text-sm font-semibold', isDone || isActive ? 'text-gray-900' : 'text-gray-400')}>
                    {label}
                  </p>
                  {timestamp && <p className="text-xs text-gray-500 mt-0.5">{timestamp}</p>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default OrderStatusTimeline;
