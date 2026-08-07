from pathlib import Path

from scripts.check_docs import broken_links


def test_aceita_link_relativo_existente(tmp_path: Path):
    destino = tmp_path / "docs" / "alvo.md"
    destino.parent.mkdir()
    destino.write_text("# Alvo\n", encoding="utf-8")
    origem = tmp_path / "README.md"
    origem.write_text("[documento](docs/alvo.md)\n", encoding="utf-8")

    assert broken_links(origem, tmp_path) == []


def test_reporta_link_local_inexistente(tmp_path: Path):
    origem = tmp_path / "README.md"
    origem.write_text("[ausente](docs/ausente.md#secao)\n", encoding="utf-8")

    assert broken_links(origem, tmp_path) == [
        ("docs/ausente.md#secao", (tmp_path / "docs" / "ausente.md").resolve())
    ]


def test_ignora_url_ancora_e_bloco_de_codigo(tmp_path: Path):
    origem = tmp_path / "README.md"
    origem.write_text(
        "[web](https://example.com) [seção](#titulo)\n"
        "```markdown\n[exemplo](arquivo-que-nao-existe.md)\n```\n",
        encoding="utf-8",
    )

    assert broken_links(origem, tmp_path) == []


def test_valida_src_html_e_caminho_codificado(tmp_path: Path):
    imagem = tmp_path / "assets" / "marca seriema.svg"
    imagem.parent.mkdir()
    imagem.write_text("<svg/>\n", encoding="utf-8")
    origem = tmp_path / "README.md"
    origem.write_text('<img src="assets/marca%20seriema.svg">\n', encoding="utf-8")

    assert broken_links(origem, tmp_path) == []
