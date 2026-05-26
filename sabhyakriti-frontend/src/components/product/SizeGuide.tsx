import { useAppDispatch, useAppSelector } from '@/store/store';
import { closeSizeGuide } from '@/store/slices/uiSlice';
import { X } from 'lucide-react';

const measurements = [
  { name: 'Saree Length', standard: '5.5 meters', festive: '6.3 meters', bridal: '7+ meters' },
  { name: 'Blouse Piece', standard: '0.8 m', festive: '0.8–1 m', bridal: '1 m' },
  { name: 'Fall & Pico', standard: 'Optional', festive: 'Recommended', bridal: 'Included' },
];

const wrapStyles = [
  { name: 'Nivi Style', description: 'Most popular draping style from Andhra Pradesh', suitable: 'All fabrics' },
  { name: 'Bengali Style', description: 'No pleats; elegant side draping', suitable: 'Cotton, Silk' },
  { name: 'Gujarati Style', description: 'Pallu over right shoulder', suitable: 'Silk, Georgette' },
  { name: 'Maharashtrian', description: '9-yard dhoti style', suitable: 'Cotton' },
];

const SizeGuide: React.FC = () => {
  const dispatch = useAppDispatch();
  const open = useAppSelector((s) => s.ui.modals.sizeGuide.open);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" data-testid="size-guide-modal">
      <div className="absolute inset-0 bg-black/50" onClick={() => dispatch(closeSizeGuide())} />
      <div className="relative bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Saree Size Guide</h2>
          <button
            onClick={() => dispatch(closeSizeGuide())}
            data-testid="size-guide-close"
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close size guide"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Measurements Table */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">Standard Measurements</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="text-left py-2 px-3 border border-gray-200 font-semibold text-gray-700">Measurement</th>
                    <th className="text-center py-2 px-3 border border-gray-200 font-semibold text-gray-700">Standard</th>
                    <th className="text-center py-2 px-3 border border-gray-200 font-semibold text-gray-700">Festive</th>
                    <th className="text-center py-2 px-3 border border-gray-200 font-semibold text-gray-700">Bridal</th>
                  </tr>
                </thead>
                <tbody>
                  {measurements.map((row) => (
                    <tr key={row.name}>
                      <td className="py-2 px-3 border border-gray-200 text-gray-700">{row.name}</td>
                      <td className="py-2 px-3 border border-gray-200 text-center">{row.standard}</td>
                      <td className="py-2 px-3 border border-gray-200 text-center">{row.festive}</td>
                      <td className="py-2 px-3 border border-gray-200 text-center">{row.bridal}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Draping Styles */}
          <div>
            <h3 className="font-semibold text-gray-800 mb-3">Popular Draping Styles</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {wrapStyles.map((style) => (
                <div key={style.name} className="bg-teal-50 rounded-xl p-3">
                  <h4 className="font-medium text-teal-800">{style.name}</h4>
                  <p className="text-xs text-teal-600 mt-0.5">{style.description}</p>
                  <p className="text-xs text-gray-500 mt-1">Best for: {style.suitable}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Tips */}
          <div className="bg-saffron-50 rounded-xl p-4">
            <h3 className="font-semibold text-saffron-700 mb-2">Tips for Perfect Fit</h3>
            <ul className="text-sm text-gray-700 space-y-1">
              <li>• Measure from shoulder to floor for saree length</li>
              <li>• Add 20-25cm to floor length for comfortable draping</li>
              <li>• Petticoat should match saree color for best results</li>
              <li>• Get blouse stitched by a professional for perfect fit</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SizeGuide;
