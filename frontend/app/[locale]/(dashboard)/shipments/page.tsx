import ShipmentsTable from "@/components/ShipmentsTable";
import { useTranslations } from "next-intl";

export default function ShipmentsPage() {
    const t = useTranslations('Shipments');
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900">{t('title')}</h2>
            <ShipmentsTable />
        </div>
    );
}
