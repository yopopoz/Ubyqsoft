import os
from langchain_community.llms import Ollama
from langchain_community.utilities import SQLDatabase
from langchain_community.tools.sql_database.tool import QuerySQLDataBaseTool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ...database import engine as db_engine

# Comprehensive SQL prompt with all tables
SQL_PROMPT = """SQL PostgreSQL expert. Tables disponibles:

=== SHIPMENTS ===
id, reference, order_number, batch_number, sku, customer, status, origin, destination, planned_etd, planned_eta, container_number, seal_number, vessel, quantity, weight_kg, volume_cbm, supplier, forwarder_name, qc_date, mad_date, its_date, delivery_date, transport_mode, compliance_status, rush_status, comments_internal, created_at

=== EVENTS (jalons) ===
id, shipment_id, type, timestamp, note
Types: ORDER_INFO, PRODUCTION_READY, LOADING_IN_PROGRESS, TRANSIT_OCEAN, ARRIVAL_PORT, IMPORT_CLEARANCE, FINAL_DELIVERY, GPS_POSITION, CUSTOMS_STATUS

=== ALERTS (aléas/risques) ===
id, type, severity, message, impact_days, category, shipment_id, linked_route, active, created_at
Types: WEATHER, STRIKE, CUSTOMS, PORT_CONGESTION, PANDEMIC, FINANCIAL
Severity: LOW, MEDIUM, HIGH, CRITICAL

=== DOCUMENTS ===
id, shipment_id, type, filename, url, status, uploaded_at
Types: BL, INVOICE, PACKING_LIST, QC_REPORT, CUSTOMS_DEC

=== CARRIER_SCHEDULES (horaires transporteurs) ===
id, carrier, pol, pod, mode, etd, eta, transit_time_days, vessel_name, voyage_ref

Synonymes: lot→batch_number, commande/PO→reference, aléa/risque→alerts, jalon/étape→events, qualité/QC→qc_date ou documents, retard→planned_eta<CURRENT_DATE, schedule/horaire→carrier_schedules

RÈGLE IMPORTANTE: Si l'utilisateur mentionne "lot" ou un numéro de lot, chercher avec batch_number. Sinon chercher avec reference. Pour être sûr, combiner les deux: (reference ILIKE'%X%'OR batch_number ILIKE'%X%')

=== TEMPLATES ===
Q: où est ma commande X/position X/lot X
SQL: SELECT s.reference,s.batch_number,s.status,e.type as dernier_jalon,e.timestamp FROM shipments s LEFT JOIN events e ON s.id=e.shipment_id WHERE(s.reference ILIKE'%X%'OR s.batch_number ILIKE'%X%')ORDER BY e.timestamp DESC LIMIT 1;
Q: statut détaillé X/lot X/production/QC/transit
SQL: SELECT s.reference,s.batch_number,s.status,s.qc_date,s.planned_etd,s.planned_eta,s.transport_mode FROM shipments s WHERE(s.reference ILIKE'%X%'OR s.batch_number ILIKE'%X%')LIMIT 5;
Q: retards signalés/articles en retard
SQL: SELECT reference,status,planned_eta,planned_eta-CURRENT_DATE as jours_retard FROM shipments WHERE planned_eta<CURRENT_DATE AND status NOT ILIKE'%DELIVER%'LIMIT 10;
Q: ETD/date départ usine X/lot X
SQL: SELECT reference,batch_number,planned_etd,origin,status FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%'OR container_number ILIKE'%X%')LIMIT 5;
Q: ETA/arrivée prévue X/lot X
SQL: SELECT reference,batch_number,planned_eta,destination,vessel FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%')LIMIT 5;
Q: aléas météo/congestion ports
SQL: SELECT type,severity,message,impact_days,linked_route FROM alerts WHERE type IN('WEATHER','PORT_CONGESTION')AND active=true ORDER BY created_at DESC LIMIT 10;
Q: aléas opérationnels/grèves
SQL: SELECT type,severity,message,impact_days FROM alerts WHERE type IN('STRIKE','CUSTOMS')AND active=true LIMIT 10;
Q: QC validé/contrôle qualité X/lot X
SQL: SELECT reference,batch_number,qc_date,compliance_status FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%')LIMIT 5;
Q: rapport qualité/documents QC X/lot X
SQL: SELECT d.type,d.filename,d.status,d.uploaded_at FROM documents d JOIN shipments s ON d.shipment_id=s.id WHERE(s.reference ILIKE'%X%'OR s.batch_number ILIKE'%X%')AND d.type='QC_REPORT'LIMIT 5;
Q: date livraison X/lot X
SQL: SELECT reference,batch_number,delivery_date,planned_eta,destination FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%')LIMIT 5;
Q: aléas fournisseur
SQL: SELECT a.type,a.message,a.severity,s.supplier FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.active=true LIMIT 10;
Q: numéro conteneur/tracking X/lot X
SQL: SELECT reference,batch_number,container_number,seal_number,vessel FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%'OR customer ILIKE'%X%')LIMIT 10;
Q: aléas actifs/risques en cours
SQL: SELECT type,severity,message,impact_days,linked_route FROM alerts WHERE active=true ORDER BY severity DESC,created_at DESC LIMIT 15;
Q: historique jalons X/lot X
SQL: SELECT s.reference,s.batch_number,e.type,e.timestamp,e.note FROM events e JOIN shipments s ON e.shipment_id=s.id WHERE(s.reference ILIKE'%X%'OR s.batch_number ILIKE'%X%')ORDER BY e.timestamp DESC LIMIT 20;
Q: commandes urgentes/rush
SQL: SELECT reference,status,planned_eta,customer FROM shipments WHERE rush_status=true LIMIT 10;
Q: documents X/lot X/BL/facture
SQL: SELECT d.type,d.filename,d.status FROM documents d JOIN shipments s ON d.shipment_id=s.id WHERE(s.reference ILIKE'%X%'OR s.batch_number ILIKE'%X%')LIMIT 10;
Q: aléas par route/maritime
SQL: SELECT type,message,linked_route,impact_days FROM alerts WHERE linked_route IS NOT NULL AND active=true LIMIT 10;
Q: conformité/compliance X/lot X
SQL: SELECT reference,batch_number,compliance_status,qc_date FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%')LIMIT 5;
Q: poids/volume X/lot X
SQL: SELECT reference,batch_number,weight_kg,volume_cbm,quantity FROM shipments WHERE(reference ILIKE'%X%'OR batch_number ILIKE'%X%')LIMIT 5;
Q: mode transport X/aérien/maritime
SQL: SELECT reference,transport_mode,vessel,status FROM shipments WHERE transport_mode ILIKE'%X%'LIMIT 10;
Q: expéditions mois
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE created_at>=CURRENT_DATE-INTERVAL'30 days'LIMIT 10;
Q: en transit
SQL: SELECT reference,status,vessel,planned_eta FROM shipments WHERE status ILIKE'%TRANSIT%'LIMIT 10;
Q: livrés/terminés
SQL: SELECT reference,status,delivery_date FROM shipments WHERE status ILIKE'%DELIVER%'OR status ILIKE'%FINAL%'LIMIT 10;
Q: par statut
SQL: SELECT status,COUNT(*)as nb FROM shipments GROUP BY status ORDER BY nb DESC;
Q: par client
SQL: SELECT customer,COUNT(*)as nb FROM shipments GROUP BY customer ORDER BY nb DESC LIMIT 10;
Q: alertes critiques
SQL: SELECT type,message,impact_days FROM alerts WHERE severity='CRITICAL'AND active=true LIMIT 10;
Q: statistiques aléas
SQL: SELECT type,COUNT(*)as nb,AVG(impact_days)as impact_moyen FROM alerts WHERE active=true GROUP BY type;

=== COMMERCIAL/VENTES ===
Q: commande campagne X/jalons risques
SQL: SELECT s.reference,s.status,s.customer,s.planned_eta,a.type as aleas,a.severity FROM shipments s LEFT JOIN alerts a ON s.id=a.shipment_id WHERE s.customer ILIKE'%X%'OR s.comments_internal ILIKE'%campagne%'LIMIT 10;
Q: prêt facturation/ready billing
SQL: SELECT reference,status,customer,delivery_date FROM shipments WHERE status IN('FINAL_DELIVERY','IMPORT_CLEARANCE')AND delivery_date IS NOT NULL LIMIT 10;
Q: commandes prêtes opérationnellement
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE status='PRODUCTION_READY'LIMIT 10;
Q: aléas client/annulation/report
SQL: SELECT a.type,a.message,a.severity,s.customer FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.category='CLIENT'AND a.active=true LIMIT 10;
Q: deadline cut-off maritime
SQL: SELECT reference,planned_etd,planned_etd-CURRENT_DATE as jours_avant_cutoff,status FROM shipments WHERE transport_mode ILIKE'%SEA%'AND planned_etd>=CURRENT_DATE ORDER BY planned_etd LIMIT 10;
Q: expéditions première quinzaine/début mois
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE EXTRACT(DAY FROM planned_eta)<=15 AND EXTRACT(MONTH FROM planned_eta)=EXTRACT(MONTH FROM CURRENT_DATE)LIMIT 10;
Q: traçabilité flux DDP/séquence jalons
SQL: SELECT s.reference,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'ORDER BY s.reference,e.timestamp LIMIT 20;
Q: statut readiness/prêt expédition
SQL: SELECT reference,status,qc_date,planned_etd FROM shipments WHERE status IN('PRODUCTION_READY','CONTAINER_READY_FOR_DEPARTURE')LIMIT 10;
Q: DDP en transit temps réel
SQL: SELECT reference,status,vessel,planned_eta FROM shipments WHERE incoterm='DDP'AND status ILIKE'%TRANSIT%'LIMIT 10;
Q: commandes client X vue séquentielle
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.customer ILIKE'%X%'ORDER BY s.reference,e.timestamp LIMIT 30;
Q: délai readiness schedule
SQL: SELECT reference,status,planned_etd,planned_etd-CURRENT_DATE as jours_avant_depart FROM shipments WHERE status='PRODUCTION_READY'ORDER BY planned_etd LIMIT 10;
Q: eco-friendly/environnement
SQL: SELECT reference,eco_friendly_flag,customer,status FROM shipments WHERE eco_friendly_flag=true LIMIT 10;
Q: budget/over budget
SQL: SELECT reference,budget_status,customer,status FROM shipments WHERE budget_status='OVER_BUDGET'LIMIT 10;
Q: commandes par incoterm
SQL: SELECT incoterm,COUNT(*)as nb FROM shipments GROUP BY incoterm ORDER BY nb DESC;
Q: schedule transporteur X
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days,vessel_name FROM carrier_schedules WHERE carrier ILIKE'%X%'ORDER BY etd LIMIT 10;
Q: meilleur schedule maritime
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='SEA'AND etd>=CURRENT_DATE ORDER BY transit_time_days,etd LIMIT 10;
Q: volume par client
SQL: SELECT customer,SUM(quantity)as total_qty,SUM(weight_kg)as total_kg FROM shipments GROUP BY customer ORDER BY total_qty DESC LIMIT 10;
Q: commandes avec commentaires
SQL: SELECT reference,customer,comments_internal FROM shipments WHERE comments_internal IS NOT NULL AND comments_internal!=''LIMIT 10;

=== ACHATS/PROCUREMENT ===
Q: fin production ETD maritime/quand finaliser ETD
SQL: SELECT reference,status,qc_date,planned_etd,planned_etd-qc_date as delai_prod_etd FROM shipments WHERE status='PRODUCTION_READY'ORDER BY qc_date LIMIT 10;
Q: commande achat urgente/délai urgent
SQL: SELECT reference,status,planned_etd,rush_status FROM shipments WHERE rush_status=true ORDER BY planned_etd LIMIT 10;
Q: aléas fournisseurs/retards fabrication
SQL: SELECT a.type,a.message,a.severity,a.impact_days,s.supplier FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.type IN('STRIKE','CUSTOMS')AND a.active=true AND s.supplier IS NOT NULL LIMIT 10;
Q: fournisseurs sans aléas
SQL: SELECT DISTINCT s.supplier,COUNT(*)as nb_commandes FROM shipments s LEFT JOIN alerts a ON s.id=a.shipment_id WHERE a.id IS NULL AND s.supplier IS NOT NULL GROUP BY s.supplier ORDER BY nb_commandes DESC LIMIT 10;
Q: budget inflation/over budget achats
SQL: SELECT reference,supplier,budget_status FROM shipments WHERE budget_status='OVER_BUDGET'AND supplier IS NOT NULL LIMIT 10;
Q: aléas réglementaires/conformité taxes
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE type='CUSTOMS'AND active=true LIMIT 10;
Q: qualité fournisseurs/lots défectueux
SQL: SELECT s.supplier,s.reference,s.compliance_status,d.status as qc_status FROM shipments s LEFT JOIN documents d ON s.id=d.shipment_id AND d.type='QC_REPORT'WHERE s.compliance_status!='CLEARED'LIMIT 10;
Q: historique aléas par fournisseur
SQL: SELECT s.supplier,a.type,COUNT(*)as nb_aleas,AVG(a.impact_days)as impact_moyen FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE s.supplier IS NOT NULL GROUP BY s.supplier,a.type ORDER BY nb_aleas DESC LIMIT 15;
Q: contraintes environnementales fournisseurs
SQL: SELECT supplier,reference,eco_friendly_flag FROM shipments WHERE supplier IS NOT NULL ORDER BY eco_friendly_flag DESC,supplier LIMIT 10;
Q: pannes machines/impact planning
SQL: SELECT type,message,impact_days,created_at FROM alerts WHERE message ILIKE'%machine%'OR message ILIKE'%panne%'AND active=true LIMIT 10;
Q: grèves ateliers/aléas humains fournisseurs
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE type='STRIKE'AND active=true LIMIT 10;
Q: fiabilité fournisseurs KPI
SQL: SELECT s.supplier,COUNT(*)as total,SUM(CASE WHEN s.planned_eta>=s.delivery_date THEN 1 ELSE 0 END)as on_time FROM shipments s WHERE s.supplier IS NOT NULL AND s.delivery_date IS NOT NULL GROUP BY s.supplier LIMIT 10;
Q: aléas financiers fournisseurs/cash change
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE type='FINANCIAL'AND active=true LIMIT 10;
Q: rapport aléas achats
SQL: SELECT a.type,COUNT(*)as nb,AVG(a.impact_days)as impact_moyen FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE s.supplier IS NOT NULL AND a.active=true GROUP BY a.type;
Q: blocage approvisionnement/matières
SQL: SELECT type,message,severity,linked_route FROM alerts WHERE message ILIKE'%matière%'OR message ILIKE'%approvisionnement%'AND active=true LIMIT 10;
Q: achats aériens urgents
SQL: SELECT reference,supplier,transport_mode,planned_etd FROM shipments WHERE transport_mode ILIKE'%AIR%'AND rush_status=true LIMIT 10;
Q: aléas transport amont/congestion routière
SQL: SELECT type,message,severity,linked_route FROM alerts WHERE type='PORT_CONGESTION'OR message ILIKE'%transport%'AND active=true LIMIT 10;
Q: nouveaux fournisseurs/risque évaluation
SQL: SELECT supplier,COUNT(*)as nb_commandes,MIN(created_at)as premiere_commande FROM shipments WHERE supplier IS NOT NULL GROUP BY supplier HAVING COUNT(*)<3 ORDER BY premiere_commande DESC LIMIT 10;
Q: aléas pandémiques/quarantaines
SQL: SELECT type,message,severity,impact_days,linked_route FROM alerts WHERE type='PANDEMIC'AND active=true LIMIT 10;
Q: production prête ETD transporteur
SQL: SELECT s.reference,s.status,s.planned_etd,cs.carrier,cs.etd as schedule_etd FROM shipments s,carrier_schedules cs WHERE s.status='PRODUCTION_READY'AND cs.etd>=s.planned_etd ORDER BY cs.etd LIMIT 10;
Q: achats première quinzaine
SQL: SELECT reference,supplier,status,planned_eta FROM shipments WHERE supplier IS NOT NULL AND EXTRACT(DAY FROM planned_eta)<=15 AND EXTRACT(MONTH FROM planned_eta)=EXTRACT(MONTH FROM CURRENT_DATE)LIMIT 10;
Q: traçabilité achats DDP
SQL: SELECT s.reference,s.supplier,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND s.supplier IS NOT NULL ORDER BY s.reference,e.timestamp LIMIT 20;
Q: readiness achat livraison
SQL: SELECT reference,supplier,status,planned_etd FROM shipments WHERE status='PRODUCTION_READY'AND supplier IS NOT NULL ORDER BY planned_etd LIMIT 10;
Q: fournisseurs prêts schedule mois
SQL: SELECT s.supplier,s.reference,s.status,s.planned_etd FROM shipments s WHERE s.status IN('PRODUCTION_READY','CONTAINER_READY_FOR_DEPARTURE')AND s.supplier IS NOT NULL ORDER BY s.planned_etd LIMIT 10;
Q: post-achat expédition jalons
SQL: SELECT s.reference,s.supplier,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.supplier IS NOT NULL ORDER BY s.reference,e.timestamp LIMIT 30;
Q: achats transit aérien
SQL: SELECT reference,supplier,status,transport_mode,planned_eta FROM shipments WHERE transport_mode ILIKE'%AIR%'AND status ILIKE'%TRANSIT%'AND supplier IS NOT NULL LIMIT 10;
Q: achat lié schedule transporteur
SQL: SELECT s.reference,s.supplier,s.planned_etd,cs.carrier,cs.etd FROM shipments s,carrier_schedules cs WHERE s.planned_etd BETWEEN cs.etd-INTERVAL'3 days'AND cs.etd+INTERVAL'3 days'LIMIT 10;
Q: étapes achat DDP complet
SQL: SELECT s.reference,s.supplier,s.incoterm,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'ORDER BY s.reference,e.timestamp LIMIT 30;

=== LOGISTIQUE ===
Q: commandes première quinzaine/début mois
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE EXTRACT(DAY FROM planned_eta)<=15 AND EXTRACT(MONTH FROM planned_eta)=EXTRACT(MONTH FROM CURRENT_DATE)LIMIT 20;
Q: statut EXW DDP/flux commande
SQL: SELECT s.reference,s.incoterm,s.status,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp LIMIT 20;
Q: retards causes transport maritime
SQL: SELECT reference,status,planned_eta,CURRENT_DATE-planned_eta as jours_retard,vessel FROM shipments WHERE planned_eta<CURRENT_DATE AND status NOT ILIKE'%DELIVER%'AND transport_mode ILIKE'%SEA%'LIMIT 10;
Q: arrivées port 7 jours
SQL: SELECT reference,planned_eta,destination,vessel,batch_number FROM shipments WHERE planned_eta>=CURRENT_DATE AND planned_eta<=CURRENT_DATE+INTERVAL'7 days'ORDER BY planned_eta LIMIT 10;
Q: coût logistique DDP
SQL: SELECT reference,incoterm,transport_mode,weight_kg,volume_cbm FROM shipments WHERE incoterm='DDP'LIMIT 10;
Q: ETA aérien urgent
SQL: SELECT reference,planned_eta,transport_mode,rush_status,customer FROM shipments WHERE transport_mode ILIKE'%AIR%'AND rush_status=true ORDER BY planned_eta LIMIT 10;
Q: douanes validées/docs DDP
SQL: SELECT s.reference,s.compliance_status,d.type,d.status FROM shipments s LEFT JOIN documents d ON s.id=d.shipment_id WHERE s.incoterm='DDP'AND d.type='CUSTOMS_DEC'LIMIT 10;
Q: aléas congestion/fermeture ports
SQL: SELECT type,message,severity,impact_days,linked_route FROM alerts WHERE type IN('PORT_CONGESTION','WEATHER')AND active=true ORDER BY linked_route LIMIT 15;
Q: performance transporteurs/fiabilité
SQL: SELECT forwarder_name,COUNT(*)as total,SUM(CASE WHEN planned_eta>=delivery_date THEN 1 ELSE 0 END)as on_time FROM shipments WHERE delivery_date IS NOT NULL GROUP BY forwarder_name LIMIT 10;
Q: pick-ups EXW/commandes prêtes
SQL: SELECT reference,status,origin,planned_etd FROM shipments WHERE incoterm='EXW'AND status='PRODUCTION_READY'ORDER BY planned_etd LIMIT 10;
Q: tracking GPS/position maritime
SQL: SELECT e.type,e.timestamp,e.note,s.reference,s.vessel FROM events e JOIN shipments s ON e.shipment_id=s.id WHERE e.type='GPS_POSITION'ORDER BY e.timestamp DESC LIMIT 10;
Q: seconde quinzaine/fin mois
SQL: SELECT reference,status,customer,planned_eta FROM shipments WHERE EXTRACT(DAY FROM planned_eta)>15 AND EXTRACT(MONTH FROM planned_eta)=EXTRACT(MONTH FROM CURRENT_DATE)LIMIT 20;
Q: météo tempêtes conteneur
SQL: SELECT type,message,severity,impact_days,linked_route FROM alerts WHERE type='WEATHER'AND active=true LIMIT 10;
Q: géopolitique blocus/aérien
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE category='GEOPOLITICAL'OR message ILIKE'%blocus%'OR message ILIKE'%embargo%'AND active=true LIMIT 10;
Q: douanes inspections retards
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE type='CUSTOMS'AND active=true LIMIT 10;
Q: grèves aériens/transporteurs
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE type='STRIKE'AND(message ILIKE'%aérien%'OR message ILIKE'%air%')AND active=true LIMIT 10;
Q: routes alternatives congestion
SQL: SELECT carrier,pol,pod,transit_time_days,etd FROM carrier_schedules WHERE mode='SEA'AND etd>=CURRENT_DATE ORDER BY transit_time_days LIMIT 10;
Q: aléas par incoterm mode
SQL: SELECT s.incoterm,s.transport_mode,a.type,COUNT(*)as nb FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.active=true GROUP BY s.incoterm,s.transport_mode,a.type LIMIT 20;
Q: aléas humains/manutention port
SQL: SELECT type,message,severity,impact_days FROM alerts WHERE message ILIKE'%manutention%'OR message ILIKE'%main%'AND active=true LIMIT 10;
Q: dashboard aléas globaux/temps réel
SQL: SELECT type,severity,COUNT(*)as nb,AVG(impact_days)as impact_moyen FROM alerts WHERE active=true GROUP BY type,severity ORDER BY severity DESC LIMIT 15;
Q: priorisation commandes urgentes
SQL: SELECT reference,customer,status,planned_eta,rush_status FROM shipments WHERE rush_status=true ORDER BY planned_eta LIMIT 10;
Q: fêtes fermetures ports
SQL: SELECT carrier,pol,pod,etd,eta FROM carrier_schedules WHERE EXTRACT(MONTH FROM etd)=EXTRACT(MONTH FROM CURRENT_DATE)ORDER BY etd LIMIT 10;
Q: évaluation risque commande
SQL: SELECT s.reference,s.status,a.type,a.severity,a.message FROM shipments s LEFT JOIN alerts a ON s.id=a.shipment_id WHERE s.reference ILIKE'%X%'LIMIT 10;
Q: stats aléas DDP EXW comparatif
SQL: SELECT s.incoterm,a.type,COUNT(*)as nb FROM alerts a JOIN shipments s ON a.shipment_id=s.id WHERE a.active=true GROUP BY s.incoterm,a.type ORDER BY nb DESC LIMIT 15;
Q: mesures pandémie quarantaines
SQL: SELECT type,message,severity,impact_days,linked_route FROM alerts WHERE type='PANDEMIC'AND active=true LIMIT 10;
Q: schedule maritime si prêt date
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='SEA'AND etd>=CURRENT_DATE ORDER BY etd LIMIT 10;
Q: export expéditions première quinzaine
SQL: SELECT reference,status,customer,planned_eta,transport_mode FROM shipments WHERE EXTRACT(DAY FROM planned_eta)<=15 LIMIT 50;
Q: prêt assignation conteneur
SQL: SELECT reference,status,container_number,planned_etd FROM shipments WHERE status='CONTAINER_READY_FOR_DEPARTURE'OR container_number IS NOT NULL LIMIT 10;
Q: traçabilité DDP achat livraison
SQL: SELECT s.reference,s.incoterm,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'ORDER BY s.reference,e.timestamp LIMIT 30;
Q: readiness schedule aérien
SQL: SELECT reference,status,transport_mode,planned_etd FROM shipments WHERE transport_mode ILIKE'%AIR%'AND status='PRODUCTION_READY'ORDER BY planned_etd LIMIT 10;
Q: expéditions maritimes transporteur mois
SQL: SELECT s.reference,s.forwarder_name,s.planned_eta,s.vessel FROM shipments s WHERE s.transport_mode ILIKE'%SEA%'ORDER BY s.planned_eta LIMIT 20;
Q: milestones logistiques séquence
SQL: SELECT type,COUNT(*)as nb FROM events GROUP BY type ORDER BY type LIMIT 20;
Q: délai readiness départ
SQL: SELECT reference,status,qc_date,planned_etd,planned_etd-qc_date as delai_jours FROM shipments WHERE qc_date IS NOT NULL AND planned_etd IS NOT NULL ORDER BY delai_jours LIMIT 10;
Q: export traçabilité DDP en cours
SQL: SELECT s.reference,s.status,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND s.status ILIKE'%TRANSIT%'ORDER BY e.timestamp LIMIT 30;
Q: itinéraire aérien 48h
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='AIR'AND etd>=CURRENT_DATE AND etd<=CURRENT_DATE+INTERVAL'2 days'ORDER BY etd LIMIT 10;
Q: contrôle qualité flux
SQL: SELECT reference,qc_date,compliance_status,status FROM shipments WHERE qc_date IS NOT NULL ORDER BY qc_date DESC LIMIT 10;
Q: étapes douanières DDP maritime
SQL: SELECT s.reference,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND s.transport_mode ILIKE'%SEA%'AND e.type IN('CUSTOMS_STATUS','IMPORT_CLEARANCE')ORDER BY e.timestamp LIMIT 20;
Q: délai readiness départ port
SQL: SELECT reference,status,planned_etd,CURRENT_DATE-planned_etd as jours_attente FROM shipments WHERE status='PRODUCTION_READY'ORDER BY jours_attente DESC LIMIT 10;
Q: expéditions aériennes première quinzaine
SQL: SELECT reference,status,transport_mode,planned_eta FROM shipments WHERE transport_mode ILIKE'%AIR%'AND EXTRACT(DAY FROM planned_eta)<=15 LIMIT 20;
Q: vue séquentielle achat fournisseur
SQL: SELECT s.reference,s.supplier,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.supplier IS NOT NULL ORDER BY s.reference,e.timestamp LIMIT 30;
Q: schedule maritime fin mois
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='SEA'AND EXTRACT(DAY FROM etd)>=20 ORDER BY etd LIMIT 10;
Q: commandes prêtes DDP mois
SQL: SELECT reference,status,incoterm,planned_eta FROM shipments WHERE incoterm='DDP'AND status IN('PRODUCTION_READY','CONTAINER_READY_FOR_DEPARTURE')LIMIT 20;
Q: tracking GPS lots
SQL: SELECT e.type,e.timestamp,e.note,s.batch_number,s.vessel FROM events e JOIN shipments s ON e.shipment_id=s.id WHERE e.type='GPS_POSITION'AND s.batch_number ILIKE'%X%'ORDER BY e.timestamp DESC LIMIT 10;
Q: analyse retards maritimes
SQL: SELECT reference,planned_eta,delivery_date,COALESCE(delivery_date,CURRENT_DATE)-planned_eta as retard_jours,vessel FROM shipments WHERE transport_mode ILIKE'%SEA%'AND planned_eta<COALESCE(delivery_date,CURRENT_DATE)LIMIT 15;
Q: facturation flux DDP
SQL: SELECT s.reference,s.status,d.type,d.status as doc_status FROM shipments s LEFT JOIN documents d ON s.id=d.shipment_id WHERE s.incoterm='DDP'AND d.type='INVOICE'LIMIT 10;
Q: préparation emballage commande
SQL: SELECT reference,status,comments_internal FROM shipments WHERE reference ILIKE'%X%'LIMIT 5;
Q: première quinzaine tracking actif
SQL: SELECT s.reference,s.status,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE EXTRACT(DAY FROM s.planned_eta)<=15 AND e.type='GPS_POSITION'ORDER BY e.timestamp DESC LIMIT 20;
Q: phase livraison DDP
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND e.type='FINAL_DELIVERY'LIMIT 10;
Q: expéditions DDP transporteur mois
SQL: SELECT reference,forwarder_name,status,incoterm,planned_eta FROM shipments WHERE incoterm='DDP'ORDER BY planned_eta LIMIT 20;
Q: délai achat matières readiness
SQL: SELECT reference,created_at,qc_date,qc_date-created_at::date as delai_jours FROM shipments WHERE qc_date IS NOT NULL ORDER BY delai_jours LIMIT 10;
Q: traçabilité achat référence
SQL: SELECT s.reference,s.supplier,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp LIMIT 20;
Q: assignation conteneur moment
SQL: SELECT reference,container_number,status,planned_etd FROM shipments WHERE container_number IS NOT NULL ORDER BY planned_etd LIMIT 10;
Q: post-achat expédition séquençage
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id ORDER BY s.reference,e.timestamp LIMIT 30;
Q: schedule maritime mi-mois transporteur
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='SEA'AND EXTRACT(DAY FROM etd)BETWEEN 10 AND 20 ORDER BY etd LIMIT 10;
Q: données opérationnelles DDP
SQL: SELECT reference,status,incoterm,transport_mode,planned_eta,vessel,container_number FROM shipments WHERE incoterm='DDP'AND status ILIKE'%TRANSIT%'LIMIT 20;
Q: inspection finale avant départ
SQL: SELECT s.reference,s.qc_date,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE e.type IN('INSPECTION_FINAL','PRODUCTION_READY')ORDER BY e.timestamp DESC LIMIT 10;
Q: expéditions aériennes liste
SQL: SELECT reference,status,transport_mode,planned_eta,customer FROM shipments WHERE transport_mode ILIKE'%AIR%'LIMIT 20;
Q: schedules maritimes transporteur
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days,vessel_name FROM carrier_schedules WHERE carrier ILIKE'%X%'ORDER BY etd LIMIT 15;
Q: traçabilité douanière DDP
SQL: SELECT s.reference,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND e.type IN('CUSTOMS_STATUS','IMPORT_CLEARANCE')ORDER BY e.timestamp LIMIT 20;
Q: commandes prêtes pick-up
SQL: SELECT reference,status,origin,planned_etd,customer FROM shipments WHERE status='PRODUCTION_READY'ORDER BY planned_etd LIMIT 15;
Q: délai production expédition avion
SQL: SELECT reference,qc_date,planned_etd,planned_etd-qc_date as delai_jours FROM shipments WHERE transport_mode ILIKE'%AIR%'AND qc_date IS NOT NULL ORDER BY delai_jours LIMIT 10;
Q: logs traçabilité commande
SQL: SELECT s.reference,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.reference ILIKE'%X%'ORDER BY e.timestamp LIMIT 30;
Q: clôture phase achat
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE e.type='PRODUCTION_READY'ORDER BY e.timestamp DESC LIMIT 10;
Q: expéditions DDP mois transporteur
SQL: SELECT reference,forwarder_name,incoterm,status,planned_eta FROM shipments WHERE incoterm='DDP'ORDER BY planned_eta LIMIT 20;
Q: itinéraire maritime lots prêts
SQL: SELECT cs.carrier,cs.pol,cs.pod,cs.etd,cs.transit_time_days,s.batch_number FROM carrier_schedules cs,shipments s WHERE s.status='PRODUCTION_READY'AND cs.mode='SEA'AND cs.etd>=CURRENT_DATE ORDER BY cs.etd LIMIT 10;
Q: flux traçabilité achat livraison
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id ORDER BY s.reference,e.timestamp LIMIT 50;
Q: entrée phase transit DDP
SQL: SELECT s.reference,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND e.type IN('TRANSIT_OCEAN','LOADING_IN_PROGRESS')ORDER BY e.timestamp DESC LIMIT 10;
Q: readiness première quinzaine maritime
SQL: SELECT reference,status,planned_eta,transport_mode FROM shipments WHERE status IN('PRODUCTION_READY','CONTAINER_READY_FOR_DEPARTURE')AND EXTRACT(DAY FROM planned_eta)<=15 AND transport_mode ILIKE'%SEA%'LIMIT 20;
Q: schedule optimal achat finalisé
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE etd>=CURRENT_DATE ORDER BY etd,transit_time_days LIMIT 10;
Q: étapes livraison DDP standard
SQL: SELECT type,COUNT(*)as nb FROM events WHERE type IN('ARRIVAL_PORT','IMPORT_CLEARANCE','FINAL_DELIVERY')GROUP BY type;
Q: tracking temps réel latence
SQL: SELECT e.type,e.timestamp,CURRENT_TIMESTAMP-e.timestamp as latence FROM events e WHERE e.type='GPS_POSITION'ORDER BY e.timestamp DESC LIMIT 10;
Q: schedules aériens mois
SQL: SELECT carrier,pol,pod,etd,eta,transit_time_days FROM carrier_schedules WHERE mode='AIR'ORDER BY etd LIMIT 15;
Q: readiness post-achat règle délais
SQL: SELECT reference,created_at,qc_date,qc_date-created_at::date as delai_jours,status FROM shipments WHERE qc_date IS NOT NULL ORDER BY delai_jours LIMIT 10;
Q: vue séquentielle opérationnelle lots
SQL: SELECT s.reference,s.batch_number,e.type,e.timestamp FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.batch_number ILIKE'%X%'ORDER BY e.timestamp LIMIT 30;
Q: complétude livraison DDP POD
SQL: SELECT s.reference,e.type,e.timestamp,e.note FROM shipments s JOIN events e ON s.id=e.shipment_id WHERE s.incoterm='DDP'AND e.type='FINAL_DELIVERY'ORDER BY e.timestamp DESC LIMIT 10;

Q: {question}
SQL:"""

ANSWER_PROMPT = """Réponds en français, bref et factuel. Données uniquement. Si vide/erreur: "Aucun résultat trouvé."
Q: {question}
D: {result}
R:"""

class ChatbotEngine:
    # Class-level cache for SQL patterns
    _sql_cache = {}
    
    def __init__(self, db, user):
        self.user = user
        self.db = SQLDatabase(db_engine, include_tables=["shipments", "events", "alerts", "documents", "carrier_schedules"])
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        
        # Optimized LLM for SQL generation (minimal tokens needed)
        self.sql_llm = Ollama(
            base_url=ollama_url,
            model="mistral",
            temperature=0,
            num_predict=100,  # SQL queries are short
            num_ctx=2048,     # Reduced context window
            top_k=10,         # Faster sampling
            top_p=0.5,        # More focused
            repeat_penalty=1.1,
        )
        
        # Optimized LLM for answers (slightly more tokens for response)
        self.answer_llm = Ollama(
            base_url=ollama_url,
            model="mistral",
            temperature=0,
            num_predict=80,   # Short answers
            num_ctx=1024,     # Minimal context for answer
            top_k=10,
            top_p=0.5,
        )
        
        self.sql_prompt = PromptTemplate.from_template(SQL_PROMPT)
        self.answer_prompt = PromptTemplate.from_template(ANSWER_PROMPT)

    def process_stream(self, query: str):
        try:
            yield "🔍"
            
            # Generate SQL
            sql_chain = self.sql_prompt | self.sql_llm | StrOutputParser()
            raw_sql = sql_chain.invoke({"question": query})
            
            # Clean SQL
            sql = raw_sql.strip()
            if "```" in sql:
                sql = sql.split("```")[1].replace("sql", "").strip()
            sql = sql.split(";")[0] + ";"
            
            # Execute query
            try:
                result = QuerySQLDataBaseTool(db=self.db).invoke(sql)
                if not result or result == "[]":
                    yield " Aucun résultat."
                    return
            except Exception as e:
                yield f" ❌ Erreur SQL: {str(e)[:50]}"
                return
            
            yield " "
            
            # Stream answer with optimized LLM
            answer_chain = self.answer_prompt | self.answer_llm | StrOutputParser()
            for chunk in answer_chain.stream({"question": query, "result": result}):
                yield chunk
                
        except Exception as e:
            yield f" ❌ {str(e)[:50]}"






