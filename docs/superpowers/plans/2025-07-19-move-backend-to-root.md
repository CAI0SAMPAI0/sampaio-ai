# Move Backend to Root - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move all Django backend files from `backend/` subdirectory to the project root, eliminating the nested directory structure.

**Architecture:** Move all files from `backend/` to root, then update Dockerfile, docker-compose.yml, .gitignore, .dockerignore, and any other config files that reference the `backend/` path. Django's `BASE_DIR` uses `Path(__file__).resolve().parent.parent` which will continue working correctly.

**Tech Stack:** Django, Docker, Git

---

## Task 1: Move all backend files to root

**Files:**
- Move: `backend/*` → root
- Delete: `backend/` directory (after move)

**Steps:**

- [ ] **Step 1: Move all files from backend/ to root**

```powershell
# In PowerShell, from project root
Copy-Item -Path "backend\*" -Destination "." -Recurse -Force
```

- [ ] **Step 2: Remove the empty backend/ directory**

```powershell
Remove-Item -Path "backend" -Recurse -Force
```

- [ ] **Step 3: Verify move completed**

```powershell
# Verify key files exist at root
Test-Path manage.py  # Should be True
Test-Path entrypoint.sh  # Should be True
Test-Path core  # Should be True
Test-Path backend  # Should be False (deleted)
```

---

## Task 2: Update Dockerfile

**Files:**
- Modify: `Dockerfile:15-20`

**Steps:**

- [ ] **Step 1: Update Dockerfile to remove backend/ prefix**

Change lines 15-20 from:
```dockerfile
COPY backend/requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ .
```

To:
```dockerfile
COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt

# Copy all files to container
COPY . .
```

- [ ] **Step 2: Commit Dockerfile changes**

```bash
git add Dockerfile
git commit -m "refactor: update Dockerfile paths for root structure"
```

---

## Task 3: Update docker-compose.yml

**Files:**
- Modify: `docker-compose.yml:29-35`

**Steps:**

- [ ] **Step 1: Update docker-compose.yml build context and volume**

Change lines 29-35 from:
```yaml
  app:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: sampaio_ai_app
    command: sh entrypoint.sh
    volumes:
      - ./backend:/app
```

To:
```yaml
  app:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: sampaio_ai_app
    command: sh entrypoint.sh
    volumes:
      - .:/app
```

- [ ] **Step 2: Commit docker-compose.yml changes**

```bash
git add docker-compose.yml
git commit -m "refactor: update docker-compose paths for root structure"
```

---

## Task 4: Update .gitignore

**Files:**
- Modify: `.gitignore:26-28`

**Steps:**

- [ ] **Step 1: Update .gitignore paths**

Change lines 26-28 from:
```
backend/media/
backend/backups/
backend/staticfiles/
```

To:
```
media/
backups/
staticfiles/
```

- [ ] **Step 2: Commit .gitignore changes**

```bash
git add .gitignore
git commit -m "refactor: update .gitignore paths for root structure"
```

---

## Task 5: Update .dockerignore

**Files:**
- Modify: `.dockerignore:4-6`

**Steps:**

- [ ] **Step 1: Update .dockerignore paths**

Change lines 4-6 from:
```
backend/media/
backend/staticfiles/
backend/db.sqlite3
```

To:
```
media/
staticfiles/
db.sqlite3
```

- [ ] **Step 2: Commit .dockerignore changes**

```bash
git add .dockerignore
git commit -m "refactor: update .dockerignore paths for root structure"
```

---

## Task 6: Update stack.yml (if needed)

**Files:**
- Review: `stack.yml`

**Steps:**

- [ ] **Step 1: Check if stack.yml references backend/**

The stack.yml uses a pre-built image (`ghcr.io/caio/sampaio-ai-app:latest`) and doesn't reference `backend/` directly, so no changes needed.

- [ ] **Step 2: Verify stack.yml is correct**

No changes required for stack.yml.

---

## Task 7: Final verification

**Files:**
- All modified files

**Steps:**

- [ ] **Step 1: Run git status to verify all changes**

```bash
git status
```

Expected: Should show modified Dockerfile, docker-compose.yml, .gitignore, .dockerignore

- [ ] **Step 2: Run git diff to review changes**

```bash
git diff
```

Expected: Shows path updates from `backend/` to root

- [ ] **Step 3: Final commit with all changes**

```bash
git add -A
git commit -m "refactor: move backend to root directory

- Move all Django files from backend/ to project root
- Update Dockerfile COPY paths
- Update docker-compose.yml build context
- Update .gitignore and .dockerignore paths
- Simplifies project structure"
```

- [ ] **Step 4: Push changes**

```bash
git push
```
