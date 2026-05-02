import { Document, Page, Text, View, StyleSheet } from '@react-pdf/renderer';

const s = StyleSheet.create({
  page: { padding: 40, fontSize: 10, fontFamily: 'Helvetica' },
  header: { marginBottom: 20 },
  title: { fontSize: 18, fontFamily: 'Helvetica-Bold', marginBottom: 4 },
  row: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 2 },
  tableHeader: { flexDirection: 'row', borderBottomWidth: 1, borderBottomColor: '#000', paddingBottom: 4, marginBottom: 4, fontFamily: 'Helvetica-Bold' },
  col1: { flex: 3 },
  col2: { flex: 1, textAlign: 'right' },
  totalRow: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 4 },
  bold: { fontFamily: 'Helvetica-Bold' },
  section: { marginTop: 16 },
});

export interface InvoiceLine {
  id?: string;
  description: string;
  qty: number;
  unit_price_cents: number;
}

export interface InvoicePdfProps {
  invoice: {
    id: string;
    invoice_number?: string;
    patient_id: string;
    patient_name?: string;
    status: string;
    subtotal: number;
    gst: number;
    total: number;
    total_cents?: number;
    lines?: InvoiceLine[];
    created_at: string;
  };
}

export default function InvoicePdf({ invoice }: InvoicePdfProps) {
  const total = invoice.total_cents != null ? invoice.total_cents / 100 : invoice.total;
  const lines = invoice.lines ?? [];

  return (
    <Document>
      <Page size="A4" style={s.page}>
        <View style={s.header}>
          <Text style={s.title}>Dental Clinic</Text>
          <Text>Invoice #{invoice.invoice_number ?? invoice.id.slice(0, 8)}</Text>
          <Text>Date: {new Date(invoice.created_at).toLocaleDateString('en-CA')}</Text>
          <Text>Patient: {invoice.patient_name ?? invoice.patient_id}</Text>
          <Text>Status: {invoice.status}</Text>
        </View>

        {lines.length > 0 && (
          <View style={s.section}>
            <View style={s.tableHeader}>
              <Text style={s.col1}>Description</Text>
              <Text style={s.col2}>Qty</Text>
              <Text style={s.col2}>Unit</Text>
              <Text style={s.col2}>Total</Text>
            </View>
            {lines.map((line, i) => (
              <View key={line.id ?? i} style={s.row}>
                <Text style={s.col1}>{line.description}</Text>
                <Text style={s.col2}>{line.qty}</Text>
                <Text style={s.col2}>${(line.unit_price_cents / 100).toFixed(2)}</Text>
                <Text style={s.col2}>${((line.qty * line.unit_price_cents) / 100).toFixed(2)}</Text>
              </View>
            ))}
          </View>
        )}

        <View style={[s.section, { marginTop: 20 }]}>
          <View style={s.totalRow}>
            <Text>Subtotal</Text>
            <Text>${invoice.subtotal.toFixed(2)}</Text>
          </View>
          {invoice.gst > 0 && (
            <View style={s.totalRow}>
              <Text>Tax</Text>
              <Text>${invoice.gst.toFixed(2)}</Text>
            </View>
          )}
          <View style={s.totalRow}>
            <Text style={s.bold}>Total</Text>
            <Text style={s.bold}>${total.toFixed(2)}</Text>
          </View>
        </View>
      </Page>
    </Document>
  );
}
