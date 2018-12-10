#!/usr/bin/env python3
"""
MATLAB Easy installer

Requires Python >= 3.5

Copyright © 2017 Tatsunori UCHINO

This script is licensed under the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

__author__ = "Tatsunori UCHINO"

import argparse
import functools
import operator
import os
import re
import subprocess
import sys
import typing

# コードのフォーマットにはyapfを使用


class MATLABInstaller:
    """
    MATLABインストーラのクラス
    """

    "ファイルインストールキーを書いたファイル"
    FILE_INSTALL_KEY_FILE = "file_install_key.txt"

    "ライセンスファイルのファイル名"
    LICENSE_FILE_NAME = "license.dat"

    "インストーラのファイル名"
    INSTALLER_NAME = "setup.exe" if os.name == "nt" else "install"

    MATLAB_VERSION_REGEX = re.compile(r"^R(?P<year>\d+)(?P<minor>[ab])$")

    FILE_INSTALL_KEY_REGEX = re.compile(r"^\d+-\d+-\d+-\d+$")

    @staticmethod
    def find_file_in_directory(
        file_name: str, root_path: typing.Optional[str] = None
    ) -> typing.Optional[str]:
        """
        指定されたディレクトリ内で指定された名前のファイルを探して返す

        ない場合はNoneを返す
        """

        root_path_ = (
            os.getcwd() if root_path is None else root_path
        )  # not None
        return (
            os.path.join(root_path_, file_name)
            if os.path.isdir(root_path_)
            and file_name in os.listdir(root_path_)
            else None
        )

    @staticmethod
    def matlab_version_to_key(version: str):
        match = MATLABInstaller.MATLAB_VERSION_REGEX.match(version)
        # Since 3.6, can be replaced with match["year"] or match["minor"]
        return int(match.group("year")) * 2 + ord(match.group("minor"))

    def check_already_installed(self, version: str) -> bool:
        """
        MATLABが既にインストールされているかどうかを確認する
        """

        matlab_bin_default_path = (
            "C:\\Program Files\\MATLAB\\{}\\bin\\matlab.exe"
            if os.name == "nt"
            else "/usr/local/MATLAB/{}/bin/matlab"
        ).format(version)

        return os.path.exists(
            matlab_bin_default_path
            if self.install_path is None
            else self.install_path
        )

    def find_file_path(self, file_name: str) -> str:
        """
        指定された名前のファイルを探して返す

        ない場合は例外 FileNotFoundError を返す
        探す場所: カレントディレクトリ・[カレントディレクトリ]/[バージョン名(e.g. R2017a)]・スクリプトのあるディレクトリ・[スクリプトのあるディレクトリ]/[バージョン名]
        最初に見つかったものを返す
        """

        current_dir = os.getcwd()
        this_script_dir = os.path.dirname(sys.argv[0])

        directory_candidates = [
            current_dir,
            os.path.join(current_dir, self.matlab_version),
        ]
        if this_script_dir != "":
            directory_candidates += [
                this_script_dir,
                os.path.join(this_script_dir, self.matlab_version),
            ]
        result_file_paths = list(
            filter(
                lambda file: file is not None,
                map(
                    lambda file: MATLABInstaller.find_file_in_directory(
                        file_name, file
                    ),
                    directory_candidates,
                ),
            )
        )
        if not result_file_paths:
            raise FileNotFoundError(
                "No files named {} are found".format(file_name)
            )
        return result_file_paths[0]

    @staticmethod
    def find_latest_matlab_version() -> str:
        matlab_versions = [
            dir_name
            for dir_name in os.listdir()
            if os.path.isdir(dir_name)
            and MATLABInstaller.MATLAB_VERSION_REGEX.match(dir_name)
        ]
        if not matlab_versions:
            raise FileNotFoundError("There are no directories of MATLAB.")
        return max(matlab_versions, key=MATLABInstaller.matlab_version_to_key)

    def __init__(self, args):
        """
        コンストラクタ
        """

        if args.matlab_version:
            if not MATLABInstaller.MATLAB_VERSION_REGEX(args.matlab_version):
                raise ValueError(
                    args.matlab_version + " is not a valid MATLAB version."
                )
            if not os.path.isdir(args.matlab_version):
                raise NotADirectoryError(
                    "There is no directory named {}.".format(
                        args.matlab_version
                    )
                )
            self.matlab_version = args.matlab_version
        else:
            self.matlab_version = MATLABInstaller.find_latest_matlab_version()

        "インストール先のパス (None: 指定なし)"
        self.install_path = args.to

        "インストール先の実際のパス"
        self.install_real_path = (
            args.to
            if args.to is not None
            else os.path.join(
                "/usr/local/MATLAB"
                if os.name == "posix"
                else "C:\\Program Files\\MATLAB",
                self.matlab_version,
            )
        )

        "インストーラをGUIで起動するか"
        self.batch = args.batch

        self.automate = args.automate

        "再インストールするか"
        self.reinstall = args.reinstall

        "インストーラに渡すオプションを格納する辞書"
        self.options = {}

        self.add_options()

    def get_installer_cmd(self) -> typing.Tuple[str, ...]:
        """
        インストーラのコマンドを表すタプルを返す

        Windowsではsetup.exe・それ以外ではinstallを関数find_file_pathに探させて絶対パスを返す
        Windows以外のOSでrootでこのスクリプトを実行していない場合はsudoを自動的につける
        FileNotFoundErrorを投げることがある

        例:
            (r"C:\\path\\to\\matlab\\R2017a\\setup.exe", )
            ("sudo", "/path/to/matlab/R2017a/install")
        """
        installer_path = self.find_file_path(MATLABInstaller.INSTALLER_NAME)
        return (
            (installer_path,)
            if os.name == "nt" or os.getuid() == 0
            else ("sudo", installer_path)
        )

    @staticmethod
    def get_file_install_key(path: str) -> str:
        with open(path) as file:
            key = file.read().rstrip()
        if MATLABInstaller.FILE_INSTALL_KEY_REGEX.match(key):
            return key
        else:
            raise RuntimeError(
                "The file install key {} in {} is not a valid one.".format(
                    key, path
                )
            )

    def add_options(self) -> None:
        """
        MATLABに渡すオプションの追加

        どんなオプションがあるのかに関してはinstaller_input.txtを参照のこと
        """
        self.options["agreeToLicense"] = "yes"
        if self.batch:
            self.options["mode"] = "silent"
        else:
            if self.automate:
                self.options["mode"] = "automated"
                self.options["automatedModeTimeout"] = 5000
            else:
                self.options["mode"] = "interactive"
        self.options[
            "fileInstallationKey"
        ] = MATLABInstaller.get_file_install_key(
            self.find_file_path(MATLABInstaller.FILE_INSTALL_KEY_FILE)
        )
        self.options["licensePath"] = self.find_file_path(
            MATLABInstaller.LICENSE_FILE_NAME
        )
        if self.install_path is not None:
            self.options["destinationFolder"] = self.install_path

    def make_symbolic_link(self) -> None:
        """
        MATLABのシンボリックリンクを作成

        POSIXのみ/usr/local/bin/matlabを作成
        """

        if os.name == "posix":
            matlab_link = "/usr/local/bin/matlab"
            matlab_bin = os.path.join(self.install_real_path, "bin", "matlab")
            if os.path.exists(matlab_link):
                if not os.path.islink(matlab_link):
                    print(
                        matlab_link + " is not a symbolic link",
                        file=sys.stderr,
                    )
                    return
                if os.readlink(matlab_link) != matlab_bin:
                    print(
                        matlab_link + "is linked to another version of MATLAB"
                    )
                    os.remove(matlab_link)
                else:
                    print(matlab_link + "has already been created")
                    return
            subprocess.run(("sudo", "rm", "-f", matlab_link), check=True)
            subprocess.run(
                ("sudo", "ln", "-s", matlab_bin, matlab_link), check=True
            )
        else:
            print(
                "Making a symbolic link to MATLAB in /usr/local/bin"
                " is only supported for POSIX OSes."
            )

    def make_desktop_shortcut(self) -> None:
        """
        Linuxのデスクトップショートカットを作成

        他OSではメッセージのみ、何も行わない
        """

        if os.name != "posix" or os.uname().sysname != "Linux":
            print("Making a desktop shortcut is supported only for Linux.")
            return
        logo_path = "/usr/share/icons/matlab.png"
        # if not os.path.exists(logo_path):
        #     subprocess.run(
        #         ("sudo", "wget", "https://upload.wikimedia.org"
        #          "/wikipedia/commons/2/21/Matlab_Logo.png", "-O", logo_path),
        #         check=True)
        # elif not os.path.isfile(logo_path):
        #     print(logo_path + "is not a file")
        #     return

    def run(self) -> None:
        """
        MATLABインストーラを実行する
        """

        if not self.reinstall and self.check_already_installed(
            self.matlab_version
        ):
            print("MATLAB has already been installed.")
        else:
            subprocess.run(
                self.get_installer_cmd() + self.get_options_list_tuple()
            )

    def get_options_list_tuple(self) -> typing.Tuple[str, ...]:
        """
        追加されたオプションをMATLABインストーラに渡す引数リスト(タプル)に変換

        例: {"agreeToLicense": "yes", "mode": "silent"} → ("-agreeToLicense", "yes", "-mode", "silent")
        """
        return functools.reduce(
            operator.add,
            (
                ("-{}".format(key), str(val))
                for key, val in self.options.items()
            ),
            (),
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--to", "-t", help="The path where MATLAB is installed", default=None
    )
    parser.add_argument(
        "--batch",
        "-b",
        help="Run the installer without GUI",
        action="store_true",
    )
    parser.add_argument(
        "--automate", "-a", help="Automate GUI wizard", action="store_true"
    )
    parser.add_argument(
        "--reinstall", "-r", help="Reinstall MATLAB", action="store_true"
    )
    parser.add_argument(
        "--makelink",
        "-l",
        help="Make a symbolic link (for POSIX)",
        action="store_true",
    )
    parser.add_argument(
        "--matlab-version", "-m", help="MATLAB version to install"
    )
    # parser.add_argument(
    #     "--makedesktop",
    #     "-m",
    #     help="Make a desktop shortcut (for Linux)",
    #     action="store_true")
    args = parser.parse_args()
    MATLABInstaller(args).run()
