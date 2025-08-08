import datetime
from pathlib import Path
from typing import List


class Config:
    def __init__(self, home_dir: Path, dotfiles_dir: Path, backup_dir: Path, profiles: List[str], dry_run: bool):
        self.home_dir = home_dir
        self.dotfiles_dir = dotfiles_dir
        self.backup_dir = backup_dir / datetime.datetime.now().strftime("%Y.%m.%d-%H%M%S")
        self.profiles = profiles if "common" in profiles else profiles + ["common"]
        self.dry_run = dry_run

    def is_dotfile_symlink(self, path):
        return path.is_symlink() and path.readlink().is_relative_to(self.dotfiles_dir)


class SyncNode:
    def __init__(self, node_path: Path, parent):
        self.name = node_path.name if node_path else ""
        self.is_dir = node_path.is_dir() if node_path else True
        self.parent = parent
        self.profiles = []
        self.subnodes = {}

    def all_profiles(self):
        profiles = set(self.profiles)
        for subnode in self.subnodes.values():
            profiles |= subnode.all_profiles()
        return profiles

    def is_single_pofile(self):
        return len(self.all_profiles()) == 1

    def has_homed_file(self, cfg: Config):
        if not self.is_dir:
            return False
        else:
            item_home_path = self.path(cfg.home_dir)
            return item_home_path.exists() \
                and not all([item.name in self.subnodes for item in item_home_path.iterdir()]) \
                or any([subnode.has_homed_file(cfg) for subnode in self.subnodes.values()])


    def get_or_create_subnode(self, subnode_path: Path):
        subnode_name = subnode_path.name
        if subnode_name in self.subnodes:
            subnode = self.subnodes[subnode_name]
            assert subnode.is_dir == subnode_path.is_dir()
        else:
            subnode = SyncNode(subnode_path, self)
            self.subnodes[subnode_name] = subnode
        return subnode

    def subnode(self, subnode_path: Path, profile: str):
        subnode = self.get_or_create_subnode(subnode_path)
        subnode.profiles.append(profile)
        if subnode.is_dir:
            for item in subnode_path.iterdir():
                subnode.subnode(item, profile)

    def path(self, root: Path) -> Path:
        return self.parent.path(root) / self.name if self.parent else root / self.name

    def run(self, cfg: Config):
        if self.can_symlink(cfg):
            self.symlink(cfg)
        else:
            if self.is_dir:
                item_home_path = self.path(cfg.home_dir)
                if item_home_path.is_symlink() and cfg.is_dotfile_symlink(item_home_path):
                    print("Delete old profile dir link " + str(item_home_path))
                    if not cfg.dry_run:
                        item_home_path.unlink()
                for subnode in self.subnodes.values():
                    subnode.run(cfg)

    def can_symlink(self, cfg):
        if self.name == "":
            return False
        if not self.is_dir:
            return True
        has_homed_files = self.has_homed_file(cfg)
        single_profile = self.is_single_pofile()
        return not has_homed_files and single_profile

    def symlink(self, cfg: Config):
        item_profile_path = self.path(cfg.dotfiles_dir / self.profiles[0])
        item_home_path = self.path(cfg.home_dir)
        item_backup_path = self.path(cfg.backup_dir)

        if item_home_path.is_symlink() and item_home_path.readlink() == item_profile_path:
            print("Already linked " + str(item_home_path) + " to " + str(item_profile_path))
            return
        if self.need_backup(cfg):
            print("Backup " + str(item_home_path) + " to " + str(item_backup_path))
            if not cfg.dry_run:
                item_backup_path.parent.mkdir(parents=True, exist_ok=True)
                item_home_path.rename(item_backup_path)
        if item_home_path.exists(follow_symlinks=False):
            print("Remove " + str(item_home_path))
            if not cfg.dry_run:
                item_home_path.unlink()
        print("Symlink " + str(item_home_path) + " to " + str(item_profile_path))
        if not cfg.dry_run:
            item_home_path.parent.mkdir(parents=True, exist_ok=True)
            item_home_path.symlink_to(item_profile_path, self.is_dir)

    def need_backup(self, cfg):
        item_home_path = self.path(cfg.home_dir)
        return item_home_path.exists() and not cfg.is_dotfile_symlink(item_home_path)

    @staticmethod
    def create(cfg: Config):
        # noinspection PyTypeChecker
        root_node = SyncNode(None, None)
        for profile in cfg.profiles:
            profile_dir: Path = cfg.dotfiles_dir / profile
            for item in profile_dir.iterdir():
                root_node.subnode(item, profile)
        return root_node


def run(cfg: Config):
    root_node = SyncNode.create(cfg)
    root_node.run(cfg)
