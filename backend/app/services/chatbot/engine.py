import os
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# ========================================
# COMPREHENSIVE SQL PROMPT - ALL TEMPLATES
# ========================================

SQL_PROMPT = """Tu es un expert SQL PostgreSQL pour une application de suivi logistique. Génère UNIQUEMENT une requête SQL valide, sans explication.

=== TABLES DISPONIBLES ===

SHIPMENTS (expéditions - table principale):
id, reference, batch_number, order_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, seal_number, vessel, quantity, weight_kg, volume_cbm, supplier, forwarder_name, qc_date, mad_date, its_date, delivery_date, transport_mode, compliance_status, rush_status, incoterm, comments_internal, created_at

EVENTS (jalons/étapes):
id, shipment_id, type, timestamp, note
Types: ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, ARRIVAL_PORT, IMPORT_CLEARANCE, FINAL_DELIVERY, GPS_POSITION, CUSTOMS_STATUS

ALERTS (aléas/risques):
id, type, severity, message, impact_days, category, shipment_id, linked_route, active, created_at
Types: WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL
Severity: LOW, MEDIUM, HIGH, CRITICAL

DOCUMENTS:
id, shipment_id, type, filename, url, status, uploaded_at
Types: BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC

CARRIER_SCHEDULES (horaires transporteurs):
id, carrier, pol, pod, mode, etd, eta, transit_time_days, vessel_name, voyage_ref

=== DICTIONNAIRE DE SYNONYMES COMPLET ===

TERMES DE RECHERCHE:
- "où est", "position", "suivi", "tracking", "localisation", "statut", "status", "état", "state", "point sur", "update on", "news", "info sur" → rechercher dans shipments
- "commande", "order", "PO", "bon de commande", "purchase order", "ref", "référence", "reference" → chercher dans reference
- "lot", "numéro lot", "batch", "batch number", "lot number", "n° lot" → chercher dans batch_number
- "article", "produit", "sku", "item", "product" → chercher dans sku
- "client", "customer", "acheteur", "buyer" → chercher dans customer
- "fournisseur", "supplier", "vendor", "source" → chercher dans supplier

DATES:
- "ETD", "date départ", "départ usine", "quand ça part", "departure", "ship date", "date expédition", "date envoi" → planned_etd
- "ETA", "date arrivée", "arrivée prévue", "quand ça arrive", "arrival", "delivery date prévue", "livraison prévue" → planned_eta
- "livraison", "delivery", "date livraison", "delivered", "réception" → delivery_date
- "MAD", "mise à disposition", "disponibilité", "mise à dispo", "available date" → mad_date
- "ITS", "instruction", "date instruction", "instructions to ship" → its_date
- "QC", "qualité", "quality", "contrôle qualité", "quality check", "inspection" → qc_date

TRANSPORT:
- "conteneur", "container", "boîte", "box", "ctr", "cntr" → container_number
- "navire", "vessel", "bateau", "ship", "boat", "cargo" → vessel
- "maritime", "sea", "mer", "ocean", "boat", "bateau" → transport_mode ILIKE '%SEA%'
- "aérien", "air", "avion", "flight", "plane", "cargo aérien" → transport_mode ILIKE '%AIR%'
- "routier", "road", "camion", "truck", "terrestre" → transport_mode ILIKE '%ROAD%'
- "transitaire", "forwarder", "freight forwarder", "commissionnaire" → forwarder_name
- "scellé", "seal", "plomb" → seal_number

PROBLÈMES:
- "retard", "retards", "late", "delayed", "en retard", "overdue" → planned_eta < CURRENT_DATE
- "urgent", "rush", "prioritaire", "priority", "express", "hot" → rush_status = true
- "aléa", "aléas", "risque", "risques", "problème", "issue", "alert", "alerte", "incident" → alerts
- "météo", "weather", "tempête", "storm", "typhon", "ouragan" → alerts WHERE type = 'WEATHER'
- "grève", "strike", "mouvement social" → alerts WHERE type = 'STRIKE'
- "congestion", "port congestion", "engorgement", "embouteillage" → alerts WHERE type = 'PORT_CONGESTION'
- "douane", "customs", "dédouanement", "clearance" → alerts WHERE type = 'CUSTOMS'

TRAÇABILITÉ:
- "jalon", "jalons", "étape", "étapes", "milestone", "milestones", "event", "events", "historique", "timeline", "suivi" → events
- "tracking", "trace", "traçabilité", "tracing" → events
- "GPS", "position GPS", "localisation temps réel", "real-time position" → events WHERE type = 'GPS_POSITION'

DOCUMENTS:
- "doc", "docs", "document", "documents", "papiers", "paperwork", "files" → documents
- "BL", "bill of lading", "connaissement", "B/L" → documents WHERE type = 'BL'
- "facture", "invoice", "factures", "invoices" → documents WHERE type = 'INVOICE'
- "packing list", "liste colisage", "packing", "colisage" → documents WHERE type = 'PACKING_LIST'
- "rapport QC", "QC report", "rapport qualité", "quality report", "inspection report" → documents WHERE type = 'QC_REPORT'
- "déclaration douane", "customs declaration", "DAU" → documents WHERE type = 'CUSTOMS_DEC'

INCOTERMS:
- "DDP", "rendu droits acquittés", "delivered duty paid" → incoterm = 'DDP'
- "FOB", "free on board", "franco à bord" → incoterm = 'FOB'
- "EXW", "ex works", "départ usine" → incoterm = 'EXW'
- "CIF", "cost insurance freight" → incoterm = 'CIF'
- "CFR", "cost and freight" → incoterm = 'CFR'

SCHEDULES:
- "schedule", "schedules", "horaire", "horaires", "planning", "programme" → carrier_schedules
- "prochain départ", "next departure", "prochaine rotation" → carrier_schedules WHERE etd >= CURRENT_DATE
- "transit time", "temps transit", "durée transit" → transit_time_days

STATISTIQUES:
- "stats", "statistiques", "statistics", "chiffres", "numbers", "kpi", "indicateurs" → GROUP BY + COUNT
- "combien", "how many", "nombre de", "total", "count" → COUNT(*)
- "répartition", "breakdown", "distribution", "ventilation" → GROUP BY

CONFORMITÉ:
- "conforme", "compliant", "compliance", "conformité" → compliance_status
- "non conforme", "non-compliant", "rejected", "rejeté" → compliance_status contient 'NON' ou 'REJECT'

=== RÈGLES SQL ===
- Pour chercher X: WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%'
- Toujours LIMIT 10 sauf si stats/comptage
- Dates: CURRENT_DATE pour aujourd'hui
- Intervalle: CURRENT_DATE + INTERVAL '7 days'

=== TEMPLATES - RECHERCHE & STATUT ===

Q: où est ma commande X / statut X / position X / suivi X
SQL: SELECT reference, batch_number, status, planned_eta, vessel, destination FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: statut détaillé X / tout sur commande X / détails X
SQL: SELECT reference, batch_number, status, customer, origin, destination, planned_etd, planned_eta, vessel, container_number, transport_mode, incoterm FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: chercher lot X / numéro de lot X
SQL: SELECT reference, batch_number, status, customer, planned_eta FROM shipments WHERE batch_number ILIKE '%X%' LIMIT 10;

Q: chercher SKU X / article X
SQL: SELECT reference, sku, batch_number, status, quantity FROM shipments WHERE sku ILIKE '%X%' LIMIT 10;

Q: chercher order_number X / numéro commande X
SQL: SELECT reference, order_number, batch_number, customer, status FROM shipments WHERE order_number ILIKE '%X%' LIMIT 10;

=== TEMPLATES - DATES ETD/ETA ===

Q: ETD X / date départ usine X / quand part X
SQL: SELECT reference, batch_number, planned_etd, origin, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: ETA X / arrivée prévue X / quand arrive X
SQL: SELECT reference, batch_number, planned_eta, destination, vessel, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: livraison X / date livraison X
SQL: SELECT reference, batch_number, delivery_date, planned_eta, destination FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: MAD X / mise à disposition X
SQL: SELECT reference, batch_number, mad_date, planned_eta, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: ITS X / date instruction X
SQL: SELECT reference, batch_number, its_date, planned_eta, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

=== TEMPLATES - CONTENEURS & NAVIRES ===

Q: conteneur X / tracking conteneur X
SQL: SELECT reference, batch_number, container_number, seal_number, vessel, status, planned_eta FROM shipments WHERE container_number ILIKE '%X%' OR reference ILIKE '%X%' LIMIT 5;

Q: navire X / vessel X / bateau X
SQL: SELECT reference, batch_number, vessel, container_number, planned_eta, status FROM shipments WHERE vessel ILIKE '%X%' LIMIT 10;

Q: scellé X / seal X
SQL: SELECT reference, container_number, seal_number, vessel, status FROM shipments WHERE seal_number ILIKE '%X%' LIMIT 5;

=== TEMPLATES - RETARDS & URGENCES ===

Q: retards / articles en retard / late shipments
SQL: SELECT reference, batch_number, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard, customer FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND status NOT ILIKE '%FINAL%' ORDER BY jours_retard DESC LIMIT 15;

Q: commandes urgentes / rush / prioritaires
SQL: SELECT reference, batch_number, status, planned_eta, customer FROM shipments WHERE rush_status = true ORDER BY planned_eta LIMIT 15;

Q: retards maritimes / sea delays
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard, vessel FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND transport_mode ILIKE '%SEA%' ORDER BY jours_retard DESC LIMIT 10;

Q: retards aériens / air delays
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard FROM shipments WHERE planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' AND transport_mode ILIKE '%AIR%' ORDER BY jours_retard DESC LIMIT 10;

Q: retards client X
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard FROM shipments WHERE customer ILIKE '%X%' AND planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: très en retard / retard > 7 jours
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard, customer FROM shipments WHERE planned_eta < CURRENT_DATE - 7 AND status NOT ILIKE '%DELIVER%' ORDER BY jours_retard DESC LIMIT 10;

=== TEMPLATES - ALÉAS & RISQUES ===

Q: aléas actifs / risques en cours / problèmes
SQL: SELECT type, severity, message, impact_days, linked_route FROM alerts WHERE active = true ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, created_at DESC LIMIT 20;

Q: alertes critiques / critical alerts
SQL: SELECT type, message, impact_days, linked_route, created_at FROM alerts WHERE severity = 'CRITICAL' AND active = true LIMIT 15;

Q: alertes haute priorité / high severity
SQL: SELECT type, message, impact_days, linked_route FROM alerts WHERE severity IN ('CRITICAL', 'HIGH') AND active = true LIMIT 15;

Q: aléas météo / weather alerts / tempêtes
SQL: SELECT type, severity, message, impact_days, linked_route FROM alerts WHERE type = 'WEATHER' AND active = true ORDER BY severity DESC LIMIT 10;

Q: congestion ports / port congestion
SQL: SELECT type, message, impact_days, linked_route, severity FROM alerts WHERE type = 'PORT_CONGESTION' AND active = true LIMIT 10;

Q: grèves / strikes
SQL: SELECT type, message, severity, impact_days, linked_route FROM alerts WHERE type = 'STRIKE' AND active = true LIMIT 10;

Q: aléas douanes / customs issues
SQL: SELECT type, message, severity, impact_days FROM alerts WHERE type = 'CUSTOMS' AND active = true LIMIT 10;

Q: risques financiers / financial risks
SQL: SELECT type, message, severity, impact_days FROM alerts WHERE type = 'FINANCIAL' AND active = true LIMIT 10;

Q: pandémie / pandemic alerts
SQL: SELECT type, message, severity, impact_days, linked_route FROM alerts WHERE type = 'PANDEMIC' AND active = true LIMIT 10;

Q: risques par route X / aléas route X
SQL: SELECT type, message, severity, impact_days FROM alerts WHERE linked_route ILIKE '%X%' AND active = true LIMIT 10;

Q: impact total aléas / jours perdus
SQL: SELECT type, COUNT(*) as nb, SUM(impact_days) as total_impact, AVG(impact_days) as impact_moyen FROM alerts WHERE active = true GROUP BY type ORDER BY total_impact DESC;

Q: statistiques aléas / alert stats
SQL: SELECT type, severity, COUNT(*) as nb FROM alerts WHERE active = true GROUP BY type, severity ORDER BY type, severity;

Q: historique aléas / all alerts
SQL: SELECT type, severity, message, impact_days, created_at FROM alerts ORDER BY created_at DESC LIMIT 20;

=== TEMPLATES - JALONS & TRAÇABILITÉ ===

Q: historique jalons X / étapes X / events X / timeline X
SQL: SELECT e.type, e.timestamp, e.note, s.reference FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' ORDER BY e.timestamp DESC LIMIT 25;

Q: tracking GPS / position temps réel / GPS
SQL: SELECT e.type, e.timestamp, e.note, s.reference, s.vessel FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type = 'GPS_POSITION' ORDER BY e.timestamp DESC LIMIT 10;

Q: douanes / customs status / dédouanement
SQL: SELECT e.type, e.timestamp, e.note, s.reference, s.customer FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type IN ('CUSTOMS_STATUS', 'IMPORT_CLEARANCE') ORDER BY e.timestamp DESC LIMIT 10;

Q: chargement en cours / loading
SQL: SELECT e.type, e.timestamp, s.reference, s.vessel FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type = 'LOADING_IN_PROGRESS' ORDER BY e.timestamp DESC LIMIT 10;

Q: arrivées port / port arrivals
SQL: SELECT e.type, e.timestamp, s.reference, s.destination FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type = 'ARRIVAL_PORT' ORDER BY e.timestamp DESC LIMIT 10;

Q: livraisons récentes / recent deliveries
SQL: SELECT e.type, e.timestamp, s.reference, s.customer FROM events e JOIN shipments s ON e.shipment_id = s.id WHERE e.type = 'FINAL_DELIVERY' ORDER BY e.timestamp DESC LIMIT 10;

Q: dernières mises à jour / recent events
SQL: SELECT e.type, e.timestamp, e.note, s.reference FROM events e JOIN shipments s ON e.shipment_id = s.id ORDER BY e.timestamp DESC LIMIT 20;

=== TEMPLATES - DOCUMENTS ===

Q: documents X / docs X / papiers X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%' ORDER BY d.uploaded_at DESC LIMIT 10;

Q: BL X / bill of lading X / connaissement X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'BL' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

Q: facture X / invoice X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'INVOICE' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

Q: packing list X / liste colisage X
SQL: SELECT d.type, d.filename, d.status, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'PACKING_LIST' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

Q: rapport qualité X / QC report X / contrôle qualité X
SQL: SELECT d.type, d.filename, d.status, d.uploaded_at, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'QC_REPORT' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

Q: déclaration douane X / customs declaration X
SQL: SELECT d.type, d.filename, d.status, s.reference FROM documents d JOIN shipments s ON d.shipment_id = s.id WHERE d.type = 'CUSTOMS_DEC' AND (s.reference ILIKE '%X%' OR s.batch_number ILIKE '%X%') LIMIT 5;

Q: documents manquants / missing docs
SQL: SELECT s.reference, s.status FROM shipments s WHERE NOT EXISTS (SELECT 1 FROM documents d WHERE d.shipment_id = s.id) AND s.status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: documents récents / recent uploads
SQL: SELECT d.type, d.filename, s.reference, d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id = s.id ORDER BY d.uploaded_at DESC LIMIT 15;

=== TEMPLATES - QUALITÉ & CONFORMITÉ ===

Q: QC validé X / contrôle qualité X
SQL: SELECT reference, batch_number, qc_date, compliance_status, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: conformité X / compliance X
SQL: SELECT reference, batch_number, compliance_status, qc_date, status FROM shipments WHERE reference ILIKE '%X%' OR batch_number ILIKE '%X%' LIMIT 5;

Q: QC en attente / pending QC
SQL: SELECT reference, batch_number, status, planned_etd FROM shipments WHERE qc_date IS NULL AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: QC récents / recent QC
SQL: SELECT reference, batch_number, qc_date, compliance_status FROM shipments WHERE qc_date IS NOT NULL ORDER BY qc_date DESC LIMIT 10;

Q: non conforme / non-compliant / rejected QC
SQL: SELECT reference, batch_number, compliance_status, qc_date FROM shipments WHERE compliance_status ILIKE '%NON%' OR compliance_status ILIKE '%REJECT%' LIMIT 10;

Q: délai production-expédition X
SQL: SELECT reference, qc_date, planned_etd, planned_etd - qc_date as delai_jours FROM shipments WHERE qc_date IS NOT NULL AND planned_etd IS NOT NULL AND (reference ILIKE '%X%' OR batch_number ILIKE '%X%') LIMIT 5;

=== TEMPLATES - CLIENTS ===

Q: commandes client X / customer X orders
SQL: SELECT reference, batch_number, status, planned_eta, origin FROM shipments WHERE customer ILIKE '%X%' ORDER BY planned_eta LIMIT 15;

Q: retards client X / client X delays
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard FROM shipments WHERE customer ILIKE '%X%' AND planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' ORDER BY jours_retard DESC LIMIT 10;

Q: livrées client X / deliveries customer X
SQL: SELECT reference, delivery_date, status FROM shipments WHERE customer ILIKE '%X%' AND (status ILIKE '%DELIVER%' OR status ILIKE '%FINAL%') ORDER BY delivery_date DESC LIMIT 10;

Q: rush client X / urgent client X
SQL: SELECT reference, status, planned_eta FROM shipments WHERE customer ILIKE '%X%' AND rush_status = true LIMIT 10;

Q: volume client X / stats client X
SQL: SELECT customer, COUNT(*) as nb_commandes, SUM(quantity) as total_qty, SUM(weight_kg) as total_kg FROM shipments WHERE customer ILIKE '%X%' GROUP BY customer;

Q: top clients / meilleurs clients
SQL: SELECT customer, COUNT(*) as nb_commandes FROM shipments GROUP BY customer ORDER BY nb_commandes DESC LIMIT 10;

Q: liste clients / all customers
SQL: SELECT DISTINCT customer, COUNT(*) as nb FROM shipments WHERE customer IS NOT NULL GROUP BY customer ORDER BY nb DESC LIMIT 20;

=== TEMPLATES - FOURNISSEURS ===

Q: commandes fournisseur X / supplier X orders
SQL: SELECT reference, batch_number, status, planned_etd, supplier FROM shipments WHERE supplier ILIKE '%X%' ORDER BY planned_etd LIMIT 15;

Q: retards fournisseur X
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard FROM shipments WHERE supplier ILIKE '%X%' AND planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: volume fournisseur X / stats fournisseur X
SQL: SELECT supplier, COUNT(*) as nb, SUM(quantity) as total_qty FROM shipments WHERE supplier ILIKE '%X%' GROUP BY supplier;

Q: top fournisseurs / best suppliers
SQL: SELECT supplier, COUNT(*) as nb_commandes FROM shipments WHERE supplier IS NOT NULL GROUP BY supplier ORDER BY nb_commandes DESC LIMIT 10;

Q: fiabilité fournisseur X / supplier reliability
SQL: SELECT supplier, COUNT(*) as total, SUM(CASE WHEN delivery_date IS NOT NULL AND planned_eta >= delivery_date THEN 1 ELSE 0 END) as on_time FROM shipments WHERE supplier ILIKE '%X%' AND delivery_date IS NOT NULL GROUP BY supplier;

Q: liste fournisseurs
SQL: SELECT DISTINCT supplier, COUNT(*) as nb FROM shipments WHERE supplier IS NOT NULL GROUP BY supplier ORDER BY nb DESC LIMIT 20;

=== TEMPLATES - TRANSITAIRES ===

Q: commandes transitaire X / forwarder X
SQL: SELECT reference, status, forwarder_name, planned_eta FROM shipments WHERE forwarder_name ILIKE '%X%' LIMIT 15;

Q: top transitaires
SQL: SELECT forwarder_name, COUNT(*) as nb FROM shipments WHERE forwarder_name IS NOT NULL GROUP BY forwarder_name ORDER BY nb DESC LIMIT 10;

Q: performance transitaires
SQL: SELECT forwarder_name, COUNT(*) as total, SUM(CASE WHEN planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as retards FROM shipments WHERE forwarder_name IS NOT NULL GROUP BY forwarder_name ORDER BY total DESC LIMIT 10;

=== TEMPLATES - TRANSPORT & MODES ===

Q: en transit / transit shipments
SQL: SELECT reference, batch_number, vessel, planned_eta, status, destination FROM shipments WHERE status ILIKE '%TRANSIT%' ORDER BY planned_eta LIMIT 15;

Q: livrées / delivered / terminées
SQL: SELECT reference, batch_number, delivery_date, status, customer FROM shipments WHERE status ILIKE '%DELIVER%' OR status ILIKE '%FINAL%' ORDER BY delivery_date DESC LIMIT 15;

Q: expéditions maritimes / sea shipments / maritime
SQL: SELECT reference, transport_mode, vessel, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%SEA%' OR transport_mode ILIKE '%OCEAN%' ORDER BY planned_eta LIMIT 15;

Q: expéditions aériennes / air shipments / aérien
SQL: SELECT reference, transport_mode, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%AIR%' ORDER BY planned_eta LIMIT 15;

Q: expéditions terrestres / road / camion
SQL: SELECT reference, transport_mode, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%ROAD%' OR transport_mode ILIKE '%TRUCK%' ORDER BY planned_eta LIMIT 15;

Q: rail / train
SQL: SELECT reference, transport_mode, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%RAIL%' ORDER BY planned_eta LIMIT 10;

Q: multimodal
SQL: SELECT reference, transport_mode, status, planned_eta FROM shipments WHERE transport_mode ILIKE '%MULTI%' LIMIT 10;

Q: production prête / ready to ship
SQL: SELECT reference, status, customer, planned_etd FROM shipments WHERE status = 'PRODUCTION_READY' ORDER BY planned_etd LIMIT 15;

Q: chargement / loading now
SQL: SELECT reference, status, vessel, origin FROM shipments WHERE status ILIKE '%LOADING%' LIMIT 10;

Q: au port / at port
SQL: SELECT reference, status, destination, planned_eta FROM shipments WHERE status ILIKE '%PORT%' OR status ILIKE '%ARRIVAL%' LIMIT 10;

Q: dédouanement / customs clearance
SQL: SELECT reference, status, destination, planned_eta FROM shipments WHERE status ILIKE '%CLEAR%' OR status ILIKE '%CUSTOMS%' OR status ILIKE '%IMPORT%' LIMIT 10;

=== TEMPLATES - SCHEDULES TRANSPORTEURS ===

Q: schedules / horaires transporteurs / carrier schedules
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days, vessel_name FROM carrier_schedules WHERE etd >= CURRENT_DATE ORDER BY etd LIMIT 15;

Q: schedules prochaine semaine / next week schedules
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days FROM carrier_schedules WHERE etd BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 ORDER BY etd LIMIT 15;

Q: meilleur schedule X vers Y / best schedule X to Y
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days, vessel_name FROM carrier_schedules WHERE pol ILIKE '%X%' AND pod ILIKE '%Y%' AND etd >= CURRENT_DATE ORDER BY transit_time_days, etd LIMIT 10;

Q: schedules maritime / sea schedules
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days, vessel_name FROM carrier_schedules WHERE mode = 'SEA' AND etd >= CURRENT_DATE ORDER BY etd LIMIT 15;

Q: schedules aérien / air schedules
SQL: SELECT carrier, pol, pod, etd, eta, transit_time_days FROM carrier_schedules WHERE mode = 'AIR' AND etd >= CURRENT_DATE ORDER BY etd LIMIT 15;

Q: transit time X vers Y
SQL: SELECT carrier, pol, pod, transit_time_days, etd FROM carrier_schedules WHERE pol ILIKE '%X%' AND pod ILIKE '%Y%' ORDER BY transit_time_days LIMIT 10;

Q: carriers / transporteurs disponibles
SQL: SELECT DISTINCT carrier, mode, COUNT(*) as nb_schedules FROM carrier_schedules WHERE etd >= CURRENT_DATE GROUP BY carrier, mode ORDER BY nb_schedules DESC;

=== TEMPLATES - ARRIVÉES PRÉVUES ===

Q: arrivées aujourd'hui / arriving today
SQL: SELECT reference, planned_eta, destination, vessel, customer FROM shipments WHERE DATE(planned_eta) = CURRENT_DATE ORDER BY planned_eta LIMIT 15;

Q: arrivées demain / arriving tomorrow
SQL: SELECT reference, planned_eta, destination, vessel FROM shipments WHERE DATE(planned_eta) = CURRENT_DATE + 1 LIMIT 15;

Q: arrivées cette semaine / arriving this week
SQL: SELECT reference, planned_eta, destination, vessel, customer FROM shipments WHERE planned_eta BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 ORDER BY planned_eta LIMIT 20;

Q: arrivées 7 jours / next 7 days arrivals
SQL: SELECT reference, planned_eta, destination, vessel, status FROM shipments WHERE planned_eta BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 ORDER BY planned_eta LIMIT 20;

Q: arrivées 30 jours / next month arrivals
SQL: SELECT reference, planned_eta, destination, status FROM shipments WHERE planned_eta BETWEEN CURRENT_DATE AND CURRENT_DATE + 30 ORDER BY planned_eta LIMIT 30;

Q: arrivées ce mois / monthly arrivals
SQL: SELECT reference, planned_eta, destination FROM shipments WHERE EXTRACT(MONTH FROM planned_eta) = EXTRACT(MONTH FROM CURRENT_DATE) AND EXTRACT(YEAR FROM planned_eta) = EXTRACT(YEAR FROM CURRENT_DATE) ORDER BY planned_eta LIMIT 30;

Q: départs cette semaine / departures this week
SQL: SELECT reference, planned_etd, origin, vessel FROM shipments WHERE planned_etd BETWEEN CURRENT_DATE AND CURRENT_DATE + 7 ORDER BY planned_etd LIMIT 20;

=== TEMPLATES - DDP & INCOTERMS ===

Q: commandes DDP
SQL: SELECT reference, status, incoterm, planned_eta, customer FROM shipments WHERE incoterm = 'DDP' ORDER BY planned_eta LIMIT 15;

Q: DDP en transit
SQL: SELECT reference, status, vessel, planned_eta FROM shipments WHERE incoterm = 'DDP' AND status ILIKE '%TRANSIT%' LIMIT 10;

Q: DDP en retard
SQL: SELECT reference, status, planned_eta, CURRENT_DATE - planned_eta as jours_retard FROM shipments WHERE incoterm = 'DDP' AND planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' LIMIT 10;

Q: FOB orders
SQL: SELECT reference, status, incoterm, planned_eta FROM shipments WHERE incoterm = 'FOB' LIMIT 15;

Q: EXW orders
SQL: SELECT reference, status, incoterm, planned_eta FROM shipments WHERE incoterm = 'EXW' LIMIT 15;

Q: CIF orders
SQL: SELECT reference, status, incoterm, planned_eta FROM shipments WHERE incoterm = 'CIF' LIMIT 15;

Q: commandes par incoterm / incoterm breakdown
SQL: SELECT incoterm, COUNT(*) as nb FROM shipments WHERE incoterm IS NOT NULL GROUP BY incoterm ORDER BY nb DESC;

=== TEMPLATES - STATISTIQUES GÉNÉRALES ===

Q: stats par statut / status breakdown
SQL: SELECT status, COUNT(*) as nb FROM shipments GROUP BY status ORDER BY nb DESC;

Q: stats par client / customer breakdown
SQL: SELECT customer, COUNT(*) as nb FROM shipments GROUP BY customer ORDER BY nb DESC LIMIT 15;

Q: stats par fournisseur / supplier breakdown
SQL: SELECT supplier, COUNT(*) as nb FROM shipments WHERE supplier IS NOT NULL GROUP BY supplier ORDER BY nb DESC LIMIT 15;

Q: stats par transporteur / forwarder breakdown
SQL: SELECT forwarder_name, COUNT(*) as nb FROM shipments WHERE forwarder_name IS NOT NULL GROUP BY forwarder_name ORDER BY nb DESC LIMIT 10;

Q: stats par mode / transport mode breakdown
SQL: SELECT transport_mode, COUNT(*) as nb FROM shipments WHERE transport_mode IS NOT NULL GROUP BY transport_mode ORDER BY nb DESC;

Q: stats par origine / origin breakdown
SQL: SELECT origin, COUNT(*) as nb FROM shipments WHERE origin IS NOT NULL GROUP BY origin ORDER BY nb DESC LIMIT 15;

Q: stats par destination / destination breakdown
SQL: SELECT destination, COUNT(*) as nb FROM shipments WHERE destination IS NOT NULL GROUP BY destination ORDER BY nb DESC LIMIT 15;

Q: volume total / total volume
SQL: SELECT COUNT(*) as total_shipments, SUM(quantity) as total_qty, SUM(weight_kg) as total_kg, SUM(volume_cbm) as total_cbm FROM shipments;

Q: stats mois en cours / current month stats
SQL: SELECT COUNT(*) as total, SUM(CASE WHEN status ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as livrees, SUM(CASE WHEN planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as retards FROM shipments WHERE created_at >= DATE_TRUNC('month', CURRENT_DATE);

Q: stats 30 derniers jours / last 30 days
SQL: SELECT COUNT(*) as total, SUM(CASE WHEN status ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as livrees FROM shipments WHERE created_at >= CURRENT_DATE - 30;

Q: taux de retard / delay rate
SQL: SELECT COUNT(*) as total, SUM(CASE WHEN planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' THEN 1 ELSE 0 END) as retards, ROUND(100.0 * SUM(CASE WHEN planned_eta < CURRENT_DATE AND status NOT ILIKE '%DELIVER%' THEN 1 ELSE 0 END) / COUNT(*), 1) as taux_retard_pct FROM shipments WHERE planned_eta IS NOT NULL;

Q: performance livraison / delivery performance
SQL: SELECT COUNT(*) as total, SUM(CASE WHEN delivery_date IS NOT NULL AND delivery_date <= planned_eta THEN 1 ELSE 0 END) as on_time, SUM(CASE WHEN delivery_date IS NOT NULL AND delivery_date > planned_eta THEN 1 ELSE 0 END) as late FROM shipments WHERE delivery_date IS NOT NULL;

=== TEMPLATES - COMMERCIAL / VENTES ===

Q: prêtes facturation / ready for billing
SQL: SELECT reference, status, customer, delivery_date FROM shipments WHERE status IN ('FINAL_DELIVERY', 'IMPORT_CLEARANCE') AND delivery_date IS NOT NULL ORDER BY delivery_date DESC LIMIT 15;

Q: commandes prêtes / ready orders
SQL: SELECT reference, status, customer, planned_eta FROM shipments WHERE status = 'PRODUCTION_READY' ORDER BY planned_eta LIMIT 15;

Q: pipeline client X / client X pipeline
SQL: SELECT status, COUNT(*) as nb FROM shipments WHERE customer ILIKE '%X%' GROUP BY status;

Q: valeur client X / customer X value
SQL: SELECT customer, COUNT(*) as nb, SUM(quantity) as qty, SUM(weight_kg) as kg FROM shipments WHERE customer ILIKE '%X%' GROUP BY customer;

Q: deadline cut-off maritime
SQL: SELECT reference, planned_etd, planned_etd - CURRENT_DATE as jours_avant_cutoff, status, vessel FROM shipments WHERE transport_mode ILIKE '%SEA%' AND planned_etd >= CURRENT_DATE AND status NOT ILIKE '%TRANSIT%' ORDER BY planned_etd LIMIT 15;

=== TEMPLATES - ACHATS / PROCUREMENT ===

Q: achats urgents / urgent procurement
SQL: SELECT reference, supplier, transport_mode, planned_etd, rush_status FROM shipments WHERE rush_status = true AND supplier IS NOT NULL ORDER BY planned_etd LIMIT 15;

Q: sourcing fournisseur X
SQL: SELECT reference, sku, quantity, planned_etd FROM shipments WHERE supplier ILIKE '%X%' ORDER BY planned_etd LIMIT 15;

Q: délai moyen fournisseur X
SQL: SELECT supplier, AVG(planned_eta - planned_etd) as transit_moyen FROM shipments WHERE supplier ILIKE '%X%' AND planned_etd IS NOT NULL AND planned_eta IS NOT NULL GROUP BY supplier;

Q: next PO fournisseur X / prochaine commande
SQL: SELECT reference, planned_etd, status FROM shipments WHERE supplier ILIKE '%X%' AND planned_etd >= CURRENT_DATE ORDER BY planned_etd LIMIT 5;

=== TEMPLATES - LOGISTIQUE ===

Q: capacité conteneurs / container utilization
SQL: SELECT container_number, COUNT(*) as nb_shipments, SUM(weight_kg) as total_kg, SUM(volume_cbm) as total_cbm FROM shipments WHERE container_number IS NOT NULL GROUP BY container_number ORDER BY nb_shipments DESC LIMIT 15;

Q: poids par conteneur X
SQL: SELECT container_number, SUM(weight_kg) as total_kg, SUM(volume_cbm) as total_cbm, COUNT(*) as nb_items FROM shipments WHERE container_number ILIKE '%X%' GROUP BY container_number;

Q: ports les plus utilisés
SQL: SELECT destination as port, COUNT(*) as nb FROM shipments GROUP BY destination ORDER BY nb DESC LIMIT 10;

Q: routes les plus fréquentes
SQL: SELECT origin, destination, COUNT(*) as nb FROM shipments GROUP BY origin, destination ORDER BY nb DESC LIMIT 15;

Q: lead time moyen / average lead time
SQL: SELECT AVG(planned_eta - planned_etd) as lead_time_moyen, transport_mode FROM shipments WHERE planned_etd IS NOT NULL AND planned_eta IS NOT NULL GROUP BY transport_mode;

=== FIN DES TEMPLATES ===

Q: {question}
SQL:"""

ANSWER_PROMPT = """Tu es un assistant logistique expert. Réponds en français de manière brève et factuelle.
Base-toi UNIQUEMENT sur les données fournies. N'invente JAMAIS d'information.
Si les données sont vides ou contiennent une erreur: réponds "Aucun résultat trouvé pour cette recherche."
Formate les dates en format lisible (ex: 15 janvier 2026).
Pour les retards, indique clairement le nombre de jours.

Question: {question}
Données: {result}
Réponse:"""

class ChatbotEngine:
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents", "carrier_schedules"])
        
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.llm = ChatGroq(
            api_key=groq_api_key,
            model="mixtral-8x7b-32768",  # 32K context, handles large prompts
            temperature=0,
            max_tokens=250,
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍 "
            
            # Generate SQL
            sql_chain = self.sql_prompt | self.llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean SQL
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            # Execute SQL
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
            except Exception as e:
                result = f"Erreur SQL: {str(e)}"
            
            # Generate answer
            answer_chain = self.answer_prompt | self.llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f"❌ Erreur: {str(e)}"
