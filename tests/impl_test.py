import pytest
import cwdotfiles.impl


@pytest.fixture
def cfg(tmp_path):
    dotfiles = tmp_path / "dotfiles"
    dotfiles.mkdir()

    # Common файлы
    common = dotfiles / "common"
    common.mkdir()
    (common / "file1").write_text("common")
    (common / "dir1").mkdir()
    (common / "dir1" / "file2").write_text("common")
    (common / "dir1" / "subdir1").mkdir()
    (common / "dir1" / "subdir1" / "file3").write_text("common subdir file")
    (common / "mixed_dir").mkdir()
    (common / "mixed_dir" / "common_file").write_text("common")

    # Профиль work
    work = dotfiles / "work"
    work.mkdir()
    (work / "dir1").mkdir()
    (work / "dir1" / "file3").write_text("work")
    (work / "dir1" / "subdir1").mkdir()
    (work / "dir1" / "subdir1" / "file4").write_text("work subdir file")

    (work / "work_only_dir").mkdir()
    (work / "work_only_dir" / "file4").write_text("work")
    (work / "mixed_dir").mkdir()
    (work / "mixed_dir" / "work_file").write_text("work")

    home = tmp_path / "home"
    home.mkdir()
    (home / "dir1").mkdir()
    (home / "dir1" / "file2").write_text("home dir1 file2")
    backup = tmp_path / "backup"
    cfg = cwdotfiles.impl.Config(home, dotfiles, backup, ["work"], False)
    return cfg


def test_create(tmp_path, cfg):
    root_node = cwdotfiles.impl.SyncNode.create(cfg)
    assert "" == root_node.name
    assert ["work", "common"] == root_node.subnodes["mixed_dir"].profiles
    assert ["work"] == root_node.subnodes["work_only_dir"].profiles
    assert len(root_node.subnodes["mixed_dir"].subnodes) == 2


def test_run(tmp_path, cfg):
    root_node = cwdotfiles.impl.SyncNode.create(cfg)
    root_node.run(cfg)
    assert (cfg.home_dir / "work_only_dir").is_symlink()
    assert not (cfg.home_dir / "mixed_dir").is_symlink()
    assert (cfg.backup_dir / "dir1" / "file2").exists()
