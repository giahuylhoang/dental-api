import { useForm } from 'react-hook-form';
import { fetcher } from '../../api/client';

interface FormValues {
  tooth_position: number;
  vendor: string;
  model: string;
  lot_number: string;
  surface_treatment: string;
  abutment_type: string;
  placed_date: string;
}

interface Props {
  dentureCaseId: string;
  onSaved: () => void;
}

export default function ImplantForm({ dentureCaseId, onSaved }: Props) {
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    defaultValues: { tooth_position: 1, surface_treatment: 'machined', abutment_type: 'ball' },
  });

  async function onSubmit(data: FormValues) {
    await fetcher(`/api/v2/clinical/denture-cases/${dentureCaseId}/implants`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    reset();
    onSaved();
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3 text-sm">
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Tooth position (1–32)</label>
          <input
            type="number"
            min={1}
            max={32}
            {...register('tooth_position', { required: true, min: 1, max: 32, valueAsNumber: true })}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Vendor</label>
          <input
            {...register('vendor')}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Model</label>
          <input
            {...register('model')}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Lot number *</label>
          <input
            {...register('lot_number', { required: 'Lot number is required' })}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
          {errors.lot_number && (
            <p className="mt-0.5 text-xs text-red-600">{errors.lot_number.message}</p>
          )}
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Surface treatment</label>
          <select
            {...register('surface_treatment')}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          >
            <option value="machined">Machined</option>
            <option value="SLA">SLA</option>
            <option value="RaSah">RaSah</option>
            <option value="TiUnite">TiUnite</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Abutment type</label>
          <select
            {...register('abutment_type')}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          >
            <option value="ball">Ball</option>
            <option value="bar">Bar</option>
            <option value="locator">Locator</option>
            <option value="magnet">Magnet</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-xs text-zinc-500">Placed date</label>
          <input
            type="date"
            {...register('placed_date')}
            className="w-full rounded border border-zinc-300 px-2 py-1 text-sm focus:outline-none focus:ring-1 focus:ring-zinc-400"
          />
        </div>
      </div>
      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded bg-zinc-900 px-3 py-1.5 text-xs text-white hover:bg-zinc-700 disabled:opacity-40"
      >
        Save implant
      </button>
    </form>
  );
}
