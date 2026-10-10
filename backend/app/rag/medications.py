from pathlib import Path

from unidecode import unidecode


MEDICATION_SOURCES = {
    "ritalina": "927100_ritalina_metilfenidato.pdf",
    "metilfenidato": "927100_ritalina_metilfenidato.pdf",
    "rohydorm": "102622_rohydorm_flunitrazepam.pdf",
    "flunitrazepam": "102622_rohydorm_flunitrazepam.pdf",
    "bromazepam": "880670_bromazepam.pdf",
    "aropax": "346659_aropax_paroxetina.pdf",
    "paroxetina": "346659_aropax_paroxetina.pdf",
    "venlafaxina": "666470_venlafaxina.pdf",
    "kamppi": "111824_kamppi_memantina.pdf",
    "memantina": "111824_kamppi_memantina.pdf",
    "pregabalina": "114471_pregabalina.pdf",
    "zart": "950220_zart_losartana.pdf",
    "losartana": "950220_zart_losartana.pdf",
    "selozok": "670480_selozok_metoprolol.pdf",
    "metoprolol": "670480_selozok_metoprolol.pdf",
    "propafenona": "434980_propafenona.pdf",
    "rocefin": "27049_rocefin_ceftriaxona.pdf",
    "ceftriaxona": "27049_rocefin_ceftriaxona.pdf",
    "norfloxacino": "107871_norfloxacino.pdf",
    "dicoxibe": "377500_dicoxibe_celecoxibe.pdf",
    "celecoxibe": "377500_dicoxibe_celecoxibe.pdf",
    "spidufen": "970530_spidufen_ibuprofeno.pdf",
    "ibuprofeno": "970530_spidufen_ibuprofeno.pdf",
    "tramadol": "93790_tramadol_paracetamol.pdf",
    "paracetamol": "93790_tramadol_paracetamol.pdf",
    "pantoprazol": "805950_pantoprazol.pdf",
    "volig": "108283_volig_ondansetrona.pdf",
    "ondansetrona": "108283_volig_ondansetrona.pdf",
    "vocety": "120535_vocety_levocetirizina.pdf",
    "levocetirizina": "120535_vocety_levocetirizina.pdf",
    "plaquinol": "308510_plaquinol_hidroxicloroquina.pdf",
    "hidroxicloroquina": "308510_plaquinol_hidroxicloroquina.pdf",
    "gestinol": "438950_gestinol_contraceptivo.pdf",
}


def normalizar(texto: str) -> str:
    return unidecode(texto).lower().strip()


def identificar_source(pergunta: str) -> str | None:
    pergunta_normalizada = normalizar(pergunta)

    for medicamento, source in MEDICATION_SOURCES.items():
        if medicamento in pergunta_normalizada:
            return source

    return None


def source_existe(source: str) -> bool:
    return Path(source).name in set(MEDICATION_SOURCES.values())