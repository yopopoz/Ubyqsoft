export interface Shipment {
    id: number;
    reference: string; // PO Number
    customer?: string | null;
    origin?: string | null;
    destination?: string | null;
    incoterm: string; // Default "FOB"

    planned_etd?: string | null; // ISO DateTime
    planned_eta?: string | null; // ISO DateTime

    container_number?: string | null;
    seal_number?: string | null;

    // Goods Info
    sku?: string | null;
    product_description?: string | null;
    quantity?: number | null;
    weight_kg?: number | null;
    volume_cbm?: number | null;
    nb_pallets?: number | null;
    nb_cartons?: number | null;

    // Extras
    order_number?: string | null;
    supplier?: string | null;
    incoterm_city?: string | null;
    loading_place?: string | null; // POL
    pod?: string | null; // Port of Discharge

    mad_date?: string | null; // ISO DateTime
    its_date?: string | null; // ISO DateTime

    vessel?: string | null;
    bl_number?: string | null;

    forwarder_ref?: string | null;
    pure_trade_ref?: string | null;

    interlocuteur?: string | null;
    responsable_pure_trade?: string | null;

    // Users


    status: string; // Stores last EventType values
    created_at: string; // ISO DateTime
}

export interface ShipmentCreate {
    reference: string;
    customer?: string | null;
    origin?: string | null;
    destination?: string | null;
    incoterm?: string;
    planned_etd?: string | null;
    planned_eta?: string | null;
    container_number?: string | null;
    seal_number?: string | null;
    sku?: string | null;
    product_description?: string | null;
    quantity?: number | null;
    weight_kg?: number | null;
    volume_cbm?: number | null;
    nb_pallets?: number | null;
    nb_cartons?: number | null;
    order_number?: string | null;
    supplier?: string | null;
    incoterm_city?: string | null;
    loading_place?: string | null;
    pod?: string | null;
    mad_date?: string | null;
    its_date?: string | null;
    vessel?: string | null;
    bl_number?: string | null;
    forwarder_ref?: string | null;
    pure_trade_ref?: string | null;
    interlocuteur?: string | null;
    responsable_pure_trade?: string | null;
}
