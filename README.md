# MATLAB Easy Installer

[![Build status](https://ci.appveyor.com/api/projects/status/u2h57pek9jlilotx/branch/master?svg=true)](https://ci.appveyor.com/project/tats-u/matlab-easy-installer/branch/master)

ユーザーにファイルインストールキーの入力・ライセンスファイルの指定をさせることなく、(半)自動で MATLAB のインストールを行うことができるユーティリティーです。

## 必須要件

- Python 3 (Windows で後述の exe ファイルを利用する場合は不要)
- MATLAB を、ファイルインストールキーを利用して複数台に導入する予定であること

## 使用の準備

### 1. `easy_install.py` の用意

このプロジェクトを `git clone` するか、 `easy_install.py` をダウンロードしてください。  
Windows 環境に導入する予定の場合は、Python をインストールしていない環境でも実行できる・エクスプローラーからワンクリックで実行できるようにするため、AppVeyor の「[Artifacts](https://ci.appveyor.com/project/tats-u/matlab-easy-installer/build/artifacts)」から `easy_install.exe` をダウンロードし、 `easy_install.py` と同じディレクトリに置いてください。

### 2. MATLAB のダウンロード

MATLAB のインストーラーを起動し、MATLAB アカウントでログインした後、「ダウンロードのみ」を選択し、 `easy_install.py` があるディレクトリに MATLAB のバージョンのディレクトリ(例: `R2018b`)を作成し、そこにダウンロードします。

### 3. ファイルインストールキーの準備

ファイルインストールキー(例: `1234-5678-9012`)だけを記載したテキストファイルを作成し、MATLAB のディレクトリ内に `file_install_key.txt` という名前で保存します。

### 4. ライセンスファイルの準備

同じディレクトリに `license.dat` を置いてください。

## 利用方法

### Unix 系

`sudo` 可能なアカウントで

```bash
./easy_install.py
```

を実行してください。

### Windows

`easy_install.exe`をダブルクリックで実行するか、PowerShell でフォルダを開いて

```powershell
.\easy_install.exe
```

を実行してください。

### オプション一覧

主要なオプションを以下に記載します。

| オプション                 | 説明                                                                                                                 |
| -------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| `-a`, `--automate`         | 自動でウィザードを進めます。                                                                                         |
| `-b`, `--batch`            | CUIで完全自動インストールをします。                                                                                  |
| `-l`, `--makelink`         | (Windows以外のみ、`-a`・`-b`オプションを利用している場合向け)`/usr/local/bin/matlab`にシンボリックリンクを張ります。 |
| `--matlab-version VERSION` | 最新のバージョンを自動検知するのではなく、指定したヴァージョン(ディレクトリ)のMATLABをインストールします。           |
