import ShipmentsTable from "@/components/ShipmentsTable";

export default function ShipmentsPage() {
    return (
        <div className="space-y-6">
            <h2 className="text-2xl font-bold text-slate-900">Toutes les expéditions</h2>
            <ShipmentsTable />
        </div>
    );
}
