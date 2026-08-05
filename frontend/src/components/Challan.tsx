import React, { useRef } from 'react';
import { Printer } from 'lucide-react';
import { Button } from './ui';
import type { Order } from '../types';

interface ChallanProps {
  order: Order;
  approverName?: string;
  issuedByName?: string;
  receivedByName?: string;
  companyName?: string;
  companyAddress?: string;
}

export const Challan: React.FC<ChallanProps> = ({
  order,
  approverName = '_________',
  issuedByName = '_________',
  receivedByName = '_________',
  companyName = 'CLOUD9 BEVERAGES',
  companyAddress = 'Address: La Lavado Fabrica, Plot No. K/29, Ambernath, MIDC, Anand Nagar, Ambernath (E) - 421501.',
}) => {
  const printRef = useRef<HTMLDivElement>(null);

  const handlePrint = () => {
    if (printRef.current) {
      const printWindow = window.open('', '_blank');
      if (printWindow) {
        printWindow.document.write(printRef.current.innerHTML);
        printWindow.document.close();
        printWindow.print();
      }
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = String(date.getFullYear()).slice(-2);
    return `${day}-${month}-${year}`;
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button
          onClick={handlePrint}
          className="flex items-center gap-2 bg-blue-600 text-white hover:bg-blue-700"
        >
          <Printer className="w-4 h-4" />
          Print Challan
        </Button>
      </div>

      <div
        ref={printRef}
        className="bg-white p-8 font-serif text-sm"
        style={{
          width: '8.5in',
          height: '11in',
          margin: '0 auto',
          fontFamily: 'Arial, sans-serif',
          color: '#000',
          lineHeight: '1.4',
        }}
      >
        {/* Header */}
        <div className="text-center mb-6">
          <div style={{ fontSize: '24px', fontWeight: 'bold', fontStyle: 'italic' }}>
            Cloud9 Beverages
          </div>
          <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>
            Non Returnable Challan
          </div>
        </div>

        {/* Delivery Info */}
        <table style={{ width: '100%', marginBottom: '12px', borderCollapse: 'collapse' }}>
          <tbody>
            <tr>
              <td style={{ width: '30%', paddingRight: '8px' }}>
                <span style={{ fontWeight: 'bold' }}>To:</span>{' '}
                <span style={{ textDecoration: 'underline', minWidth: '150px' }}>
                  {order.vendor?.name || 'N/A'}
                </span>
              </td>
              <td style={{ width: '40%', paddingRight: '8px' }}>
                <span style={{ fontWeight: 'bold' }}>Sr.No.:</span>{' '}
                <span style={{ textDecoration: 'underline' }}>{order.id}</span>
              </td>
            </tr>
            <tr>
              <td colSpan={2} style={{ paddingTop: '8px' }}>
                <span style={{ fontWeight: 'bold' }}>Add.:</span>{' '}
                <span style={{ textDecoration: 'underline' }}>
                  {order.vendor?.address || order.vendor?.city || 'N/A'}
                </span>
              </td>
              <td style={{ paddingLeft: '16px' }}>
                <span style={{ fontWeight: 'bold' }}>Date:</span>{' '}
                <span style={{ textDecoration: 'underline' }}>
                  {order.created_at ? formatDate(order.created_at) : '___-___-__'}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        {/* Items Table */}
        <table
          style={{
            width: '100%',
            marginBottom: '24px',
            borderCollapse: 'collapse',
            border: '1px solid #000',
          }}
        >
          <thead>
            <tr style={{ backgroundColor: '#e0e0e0' }}>
              <th
                style={{
                  border: '1px solid #000',
                  padding: '6px',
                  textAlign: 'left',
                  fontWeight: 'bold',
                  width: '5%',
                }}
              >
                Sr.No.
              </th>
              <th
                style={{
                  border: '1px solid #000',
                  padding: '6px',
                  textAlign: 'left',
                  fontWeight: 'bold',
                  width: '45%',
                }}
              >
                Description
              </th>
              <th
                style={{
                  border: '1px solid #000',
                  padding: '6px',
                  textAlign: 'left',
                  fontWeight: 'bold',
                  width: '15%',
                }}
              >
                UOM
              </th>
              <th
                style={{
                  border: '1px solid #000',
                  padding: '6px',
                  textAlign: 'center',
                  fontWeight: 'bold',
                  width: '10%',
                }}
              >
                Qty.
              </th>
              <th
                style={{
                  border: '1px solid #000',
                  padding: '6px',
                  textAlign: 'left',
                  fontWeight: 'bold',
                  width: '25%',
                }}
              >
                REMARK
              </th>
            </tr>
          </thead>
          <tbody>
            {order.items && order.items.length > 0 ? (
              order.items.map((item, idx) => (
                <tr key={item.id}>
                  <td
                    style={{
                      border: '1px solid #000',
                      padding: '8px 6px',
                      textAlign: 'center',
                    }}
                  >
                    {idx + 1}
                  </td>
                  <td style={{ border: '1px solid #000', padding: '8px 6px' }}>
                    {item.item?.name || 'N/A'}
                  </td>
                  <td style={{ border: '1px solid #000', padding: '8px 6px' }}>
                    NOs
                  </td>
                  <td
                    style={{
                      border: '1px solid #000',
                      padding: '8px 6px',
                      textAlign: 'center',
                    }}
                  >
                    {item.quantity_ordered}
                  </td>
                  <td style={{ border: '1px solid #000', padding: '8px 6px' }}>
                    {/* Empty for remarks */}
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ border: '1px solid #000', padding: '12px', textAlign: 'center' }}>
                  No items
                </td>
              </tr>
            )}
            {/* Add empty rows for manual entries */}
            {[...Array(5 - (order.items?.length || 0))].map((_, idx) => (
              <tr key={`empty-${idx}`}>
                <td style={{ border: '1px solid #000', padding: '8px 6px', height: '24px' }} />
                <td style={{ border: '1px solid #000', padding: '8px 6px' }} />
                <td style={{ border: '1px solid #000', padding: '8px 6px' }} />
                <td style={{ border: '1px solid #000', padding: '8px 6px' }} />
                <td style={{ border: '1px solid #000', padding: '8px 6px' }} />
              </tr>
            ))}
          </tbody>
        </table>

        {/* Signature Section */}
        <table style={{ width: '100%', marginTop: '32px' }}>
          <tbody>
            <tr style={{ height: '60px' }}>
              <td style={{ width: '33%', textAlign: 'center', verticalAlign: 'bottom' }}>
                <div style={{ borderTop: '1px solid #000', paddingTop: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold' }}>Approved By</div>
                </div>
              </td>
              <td style={{ width: '33%', textAlign: 'center', verticalAlign: 'bottom' }}>
                <div style={{ borderTop: '1px solid #000', paddingTop: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold' }}>Issued By</div>
                </div>
              </td>
              <td style={{ width: '33%', textAlign: 'center', verticalAlign: 'bottom' }}>
                <div style={{ borderTop: '1px solid #000', paddingTop: '4px' }}>
                  <div style={{ fontSize: '11px', fontWeight: 'bold' }}>Received By</div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>

        {/* Footer */}
        <div
          style={{
            marginTop: '24px',
            paddingTop: '12px',
            borderTop: '1px solid #000',
            fontSize: '10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <div style={{ fontWeight: 'bold', fontSize: '12px' }}>{companyName}</div>
            <div style={{ marginTop: '4px', lineHeight: '1.3' }}>
              {companyAddress}
            </div>
          </div>
          <div style={{ textAlign: 'right', fontWeight: 'bold' }}>LLF</div>
        </div>
      </div>
    </div>
  );
};

export default Challan;
