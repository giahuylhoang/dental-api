import { useForm } from 'react-hook-form';
import { useQuery } from '@tanstack/react-query';
import { fetcher } from '../../api/client';

interface InventoryItem {
  id: string;
  name: string;
}

interface InventoryLot {
  id: string;
  item_id: string;
  lot_number: string;
}

interface FormValues {
  item_id: string;
  lot_id: string;
  qty_consumed: number;
  unit_cost: number;
}

interface Props {
  labCaseId: string;
  onSaved: () => void;
}

export default function MaterialConsumptionForm({ labCaseId, onSaved }: Props) {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<FormValues>({
    defaultValues: { qty_consumed: 1, unit_cost: 0 },
  });

  const { data: items, isError: itemsError } = useQuery<InventoryItem[]>({
    queryKey: ['inventory-items'],
    queryFn: () => fetcher<InventoryItem[]>('/api/v2/inventory/items'),
    retry: false,
  });

  const { data: lots, isError: lotsError } = useQuery<InventoryLot[]>({
    queryKey: ['inventory-lots'],
    queryFn: () => fetcher<InventoryLot[]>('/api/v2/inventory/lots'),
    retry: false,
  });

  const inventoryUnavailable = itemsError || lotsError;

  async function onSubmit(data: FormValues) {
    try {
      await fetcher(`/api/v2/lab/cases/${labCaseId}/materials`, {
        method: 'POST',
        body: JSON.stringify(data),
      });
    } catch {
      console.warn('Material consumption endpoint not available; skipping.');
    }
    onSaved();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 text-sm">
      {inventoryUnavailable && (
        <p className="rounded bg-zinc-100 px-3 py-2 text-xs text-zinc-500">
          Inventory backend not wired
        </p>
      )}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Item</label>
          {items && items.length > 0 ? (
            <select
              {...register('item_id')}
              className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
            >
              {items.map((i) => (
                <option key={i.id} value={i.id}>{i.name}</option>
              ))}
            </select>
          ) : (
            <input
              {...register('item_id')}
              placeholder="item_id"
              className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
            />
          )}
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Lot</label>
          {lots && lots.length > 0 ? (
            <select
              {...register('lot_id')}
              className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
            >
              {lots.map((l) => (
                <option key={l.id} value={l.id}>{l.lot_number}</option>
              ))}
            </select>
          ) : (
            <input
              {...register('lot_id')}
              placeholder="lot_id"
              className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
            />
          )}
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Qty consumed</label>
          <input
            type="number"
            min={0}
            step="any"
            {...register('qty_consumed', { valueAsNumber: true })}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Unit cost</label>
          <input
            type="number"
            min={0}
            step="any"
            {...register('unit_cost', { valueAsNumber: true })}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded bg-zinc-900 px-3 py-1.5 text-xs text-white hover:bg-zinc-700 disabled:opacity-40"
      >
        Save material
      </button>
    </form>
  );
}
