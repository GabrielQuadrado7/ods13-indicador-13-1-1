from PIL import Image

from ods13.estatistica import carregar_observacoes
from ods13.graficos import gerar_graficos

ESPERADOS = {"evolucao_brasil_regioes.png", "media_por_uf.png", "media_ufs_por_ano.png",
             "dispersao_brasil.png", "dispersao_norte.png", "dispersao_nordeste.png",
             "dispersao_sudeste.png", "dispersao_sul.png", "dispersao_centro_oeste.png",
             "dispersao_ufs.png", "histograma_ufs.png"}


def test_gera_todos_os_graficos(engine_carregado, tmp_path):
    arquivos = gerar_graficos(carregar_observacoes(engine_carregado), tmp_path / "g")
    assert {p.name for p in arquivos} == ESPERADOS
    for p in arquivos:
        with Image.open(p) as img:
            dpi = img.info["dpi"]
        assert round(dpi[0]) == 300 and p.stat().st_size > 10_000

