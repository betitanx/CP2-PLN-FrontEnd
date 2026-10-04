from app.memory.store import Store


def test_conexoes_fecham_e_permitem_remover_banco(tmp_path):
    caminho = tmp_path / 'descartavel.sqlite3'
    store = Store(caminho)
    store.criar()
    caminho.unlink()
    assert not caminho.exists()
