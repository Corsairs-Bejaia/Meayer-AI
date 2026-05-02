from typing import Dict, List, Any

LAYER_DEFINITIONS = {
    "L1": {"name": "Identity", "weight": 0.15, "required_min": 1},
    "L2": {"name": "Academic Qualifications", "weight": 0.20, "required_min": 1},
    "L3": {"name": "Professional Standing", "weight": 0.25, "required_min": 1},
    "L4": {"name": "Employment", "weight": 0.15, "required_min": 1},
    "L5": {"name": "Social & Financial Coverage", "weight": 0.15, "required_min": 1},
    "L6": {"name": "Active Practice", "weight": 0.10, "required_min": 0},
}

DOC_TYPE_TO_LAYER = {
    # L1: Identity
    "national_id": "L1",
    "passport": "L1",
    "driver_license": "L1",
    
    # L2: Academic
    "diplome_medecine": "L2",
    "diplome_residanat": "L2",
    "diplome_magister_master": "L2",
    "certificat_scolarite": "L2",
    "diplome_etranger_equivalence": "L2",
    "diploma": "L2",
    
    # L3: Standing
    "carte_professionnelle_medecin": "L3",
    "attestation_ordre": "L3",
    "autorisation_exercice_liberal": "L3",
    "agrement_clinique": "L3",
    "certificat_non_sanction": "L3",
    "attestation_non_condamnation": "L3",
    
    # L4: Employment
    "affiliation_attestation": "L4",
    "attestation_travail": "L4",
    "convention_etablissement_sante": "L4",
    
    # L5: Coverage
    "carte_chifa": "L5",
    "attestation_maj_cnas": "L5",
    "attestation_affiliation_casnos": "L5",
    "attestation_maj_casnos": "L5",
    
    # L6: Practice
    "ordonnance_recente": "L6",
    "cachet_professionnel": "L6",
    "lettre_recommandation": "L6",
    "attestation_stage_service": "L6",
}

def group_docs_by_layer(doc_types: List[str]) -> Dict[str, List[str]]:
    grouped = {lid: [] for lid in LAYER_DEFINITIONS}
    for dt in doc_types:
        layer = DOC_TYPE_TO_LAYER.get(dt)
        if layer:
            grouped[layer].append(dt)
    return grouped

def get_missing_layers(doc_types: List[str]) -> List[Dict[str, Any]]:
    grouped = group_docs_by_layer(doc_types)
    missing = []
    for lid, defn in LAYER_DEFINITIONS.items():
        if len(grouped[lid]) < defn["required_min"]:
            missing.append({
                "layer": lid,
                "name": defn["name"],
                "submitted": len(grouped[lid]),
                "required": defn["required_min"],
                "is_blocker": defn["required_min"] > 0
            })
    return missing
