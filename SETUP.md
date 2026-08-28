# Setting this up on GitHub

Written for someone who has not used git much. Run the commands in order.

## 1. One-time git setup

Only needed the first time you ever use git on a machine.

```
git config --global user.name "Santosh Kumar Shaw"
git config --global user.email "your.email@example.com"
```

## 2. Put the data in place

From the folder holding this repository:

```
python3 scripts/verify_dataset.py /path/to/SimulationCsvs --normalize-names
cp /path/to/SimulationCsvs/*.csv data/raw/
python3 scripts/check_data.py data/raw/*.csv
```

`verify_dataset.py` confirms all 68 runs are present and fixes the mixed
capitalisation. `check_data.py` verifies the physics of every run. Both should
finish without reporting problems. If they do report something, fix it before
going further -- it is much cheaper than fixing it after a referee finds it.

Then build the training set:

```
python3 scripts/prepare_data.py --raw data/raw --out data/resampled
```

## 3. Create the repository locally

```
git init
git add -A
git commit -m "Initial commit: DDD database, surrogate code, documentation"
```

## 4. Create the empty repository on GitHub

1. Go to https://github.com/new
2. Owner: your account. Repository name: something like
   `ddd-plasticity-surrogate`
3. Set it to **Public**
4. Do **not** tick "Add a README", "Add .gitignore" or "Choose a license" --
   this repository already has all three, and ticking them causes a conflict
5. Click "Create repository"

## 5. Push

GitHub will show you a URL. Use it here:

```
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPO.git
git branch -M main
git push -u origin main
```

You will be asked for a username and password. GitHub no longer accepts your
account password here -- you need a **personal access token**:

1. https://github.com/settings/tokens -> "Generate new token (classic)"
2. Tick the `repo` scope, generate, and copy the token
3. Paste the token when git asks for the password

## 6. Get a DOI (for the paper's Data availability section)

The manuscript promises a DOI. GitHub URLs are not permanent identifiers, so:

1. Sign in at https://zenodo.org with your GitHub account
2. Under Settings -> GitHub, switch your repository **on**
3. Back on GitHub: Releases -> "Create a new release", tag `v1.0.0`, publish
4. Zenodo archives it automatically and mints a DOI
5. Put that DOI in the Data availability section of the paper

## 7. Later changes

```
git add -A
git commit -m "describe what changed"
git push
```

## If something goes wrong

- `git status` shows what git thinks the current state is
- Nothing is lost until you push; a bad commit can be undone with
  `git reset --soft HEAD~1`
- If a file is too big (GitHub rejects over 100 MB), remove it, then
  `git add -A && git commit --amend`
