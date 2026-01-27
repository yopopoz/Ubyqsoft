import { apiFetch } from "./api";
import { Shipment, ShipmentCreate } from "../types/shipment";
import { Event, EventCreate } from "../types/event";

export const shipmentService = {
    getAll: async (token: string): Promise<Shipment[]> => {
        return apiFetch<Shipment[]>("/shipments/", { token });
    },

    getById: async (id: number | string, token: string): Promise<Shipment> => {
        return apiFetch<Shipment>(`/shipments/${id}`, { token });
    },

    create: async (data: ShipmentCreate, token: string): Promise<Shipment> => {
        return apiFetch<Shipment>("/shipments/", {
            method: "POST",
            body: JSON.stringify(data),
            token,
        });
    },

    update: async (id: number | string, data: Partial<ShipmentCreate>, token: string): Promise<Shipment> => {
        return apiFetch<Shipment>(`/shipments/${id}`, {
            method: "PUT",
            body: JSON.stringify(data),
            token,
        });
    },

    // Events related
    getEvents: async (shipmentId: number | string, token: string): Promise<Event[]> => {
        return apiFetch<Event[]>(`/events/shipments/${shipmentId}`, { token });
    },

    createEvent: async (data: EventCreate, token: string): Promise<Event> => {
        return apiFetch<Event>("/events/", {
            method: "POST",
            body: JSON.stringify(data),
            token
        })
    }
};
