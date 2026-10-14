# Git 협업 실습 작업 기록 (GIT_WORK.md)

## 1. 실습 개요 및 원격 저장소 정보

- **원격 저장소 주소**: [https://github.com/mmmphyun/git-collaboration-practice](https://github.com/mmmphyun/git-collaboration-practice)
- **로컬 작업 폴더**:
  - 민수 역할 폴더: `c:/work/git-practice-minsu`
  - 지윤 역할 폴더: `c:/work/git-practice-jiyun`
- **협업 전략**: GitHub Flow 기반 (`main` 브랜치 + 기능별 작업 브랜치)

---

## 2. 작업 브랜치 및 풀 리퀘스트 (PR) 목록

| 구분 | PR 번호 및 링크 | Head 브랜치 | Base 브랜치 | 병합 방식 | 상태 | 주요 작업 내용 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PR 1** | [#1](https://github.com/mmmphyun/git-collaboration-practice/pull/1) | `feature/minsu` | `main` | Merge commit | Merged | 민수 작업 일지(`minsu.md`) 작성 및 보완 커밋 반영 |
| **PR 2** | [#2](https://github.com/mmmphyun/git-collaboration-practice/pull/2) | `feature/jiyun` | `main` | Merge commit | Merged | 지윤 작업 일지(`jiyun.md`) 작성 및 초기 협업 브랜치 제출 |
| **PR 3** | [#3](https://github.com/mmmphyun/git-collaboration-practice/pull/3) | `feature/checklist` | `main` | Merge commit | Merged | 최신 main 기준 협업 점검표(`checklist.md`) 추가 |

---

## 3. 실행 단계별 주요 명령 및 실제 터미널 출력 기록

### [1단계] 저장소 복제 및 초기 상태 확인
두 개의 독립된 로컬 폴더에 동일한 원격 저장소를 clone하여 동일한 `origin`을 참조하도록 설정했습니다.

```text
PS C:\work> git clone https://github.com/mmmphyun/git-collaboration-practice.git git-practice-minsu
Cloning into 'git-practice-minsu'...

PS C:\work> git clone https://github.com/mmmphyun/git-collaboration-practice.git git-practice-jiyun
Cloning into 'git-practice-jiyun'...

PS C:\work> git -C c:\work\git-practice-minsu remote -v
origin  https://github.com/mmmphyun/git-collaboration-practice.git (fetch)
origin  https://github.com/mmmphyun/git-collaboration-practice.git (push)

PS C:\work> git -C c:\work\git-practice-jiyun remote -v
origin  https://github.com/mmmphyun/git-collaboration-practice.git (fetch)
origin  https://github.com/mmmphyun/git-collaboration-practice.git (push)
```

### [2단계] 각 폴더에서 작업 브랜치 생성 및 개별 파일 커밋
민수는 `minsu.md`, 지윤은 `jiyun.md`를 각각 작성하고 커밋했습니다.

- **민수 폴더 (`git-practice-minsu`)**:
```text
PS C:\work\git-practice-minsu> git checkout -b feature/minsu
Switched to a new branch 'feature/minsu'
PS C:\work\git-practice-minsu> git add minsu.md
PS C:\work\git-practice-minsu> git commit -m "feat: 민수 작업 일지 추가"
[feature/minsu 5066a81] feat: 민수 작업 일지 추가
 1 file changed, 3 insertions(+)
 create mode 100644 minsu.md
```

- **지윤 폴더 (`git-practice-jiyun`)**:
```text
PS C:\work\git-practice-jiyun> git checkout -b feature/jiyun
Switched to a new branch 'feature/jiyun'
PS C:\work\git-practice-jiyun> git add jiyun.md
PS C:\work\git-practice-jiyun> git commit -m "feat: 지윤 작업 일지 추가"
[feature/jiyun 5abbee5] feat: 지윤 작업 일지 추가
 1 file changed, 3 insertions(+)
 create mode 100644 jiyun.md
```

### [3단계] 로컬 브랜치 전환 및 로컬 병합(Merge) 방향 검증
`main` 브랜치로 체크아웃했을 때 작업 브랜치의 파일이 보이지 않는 것을 확인한 후, `main`에서 각 작업 브랜치를 로컬 머지하여 변경 사항이 `main`으로 흡수되는 방향을 확인했습니다. (이후 원격 PR 테스트를 위해 origin 기준 원복)

- **민수 폴더 확인 로그**:
```text
PS C:\work\git-practice-minsu> git checkout main
Switched to branch 'main'
PS C:\work\git-practice-minsu> Get-ChildItem
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---        2026-10-08  오후 3:07             30 README.md

PS C:\work\git-practice-minsu> git merge feature/minsu
Updating 186a151..5066a81
Fast-forward
 minsu.md | 3 +++
 1 file changed, 3 insertions(+)
 create mode 100644 minsu.md

PS C:\work\git-practice-minsu> Get-ChildItem
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---        2026-10-08  오후 3:08             79 minsu.md
-a---        2026-10-08  오후 3:07             30 README.md
```

### [4단계] 원격 브랜치 Push 및 PR 생성 / 민수의 보완 커밋 반영
각 작업 브랜치를 푸시한 후 `gh pr create`로 PR을 생성했습니다. 민수는 PR 제출 후 추가 검토를 거쳐 보완 커밋을 동일 브랜치에 푸시하여 PR에 자동 반영되도록 했습니다.

```text
# 원격 푸시
PS C:\work\git-practice-minsu> git push -u origin feature/minsu
To https://github.com/mmmphyun/git-collaboration-practice.git
 * [new branch]      feature/minsu -> feature/minsu

PS C:\work\git-practice-jiyun> git push -u origin feature/jiyun
To https://github.com/mmmphyun/git-collaboration-practice.git
 * [new branch]      feature/jiyun -> feature/jiyun

# PR 생성
gh pr create --repo mmmphyun/git-collaboration-practice --base main --head feature/minsu --title "feat: 민수 작업 일지 추가"
https://github.com/mmmphyun/git-collaboration-practice/pull/1

gh pr create --repo mmmphyun/git-collaboration-practice --base main --head feature/jiyun --title "feat: 지윤 작업 일지 추가"
https://github.com/mmmphyun/git-collaboration-practice/pull/2

# 민수 보완 커밋 추가 및 재푸시
PS C:\work\git-practice-minsu> git add minsu.md
PS C:\work\git-practice-minsu> git commit -m "docs: 민수 작업 일지 상세 보완"
[feature/minsu b069d20] docs: 민수 작업 일지 상세 보완
 1 file changed, 2 insertions(+)
PS C:\work\git-practice-minsu> git push origin feature/minsu
   5066a81..b069d20  feature/minsu -> feature/minsu
```

### [5단계] PR 변경 사항 검토 및 병합 (Create a merge commit)
두 PR의 diff를 확인한 뒤 머지 커밋 방식으로 각각 병합을 완료했습니다.

```text
PS C:\work> gh pr merge 1 --repo mmmphyun/git-collaboration-practice --merge
PS C:\work> gh pr merge 2 --repo mmmphyun/git-collaboration-practice --merge

# 병합 상태 확인
PS C:\work> gh pr view 1 --repo mmmphyun/git-collaboration-practice --json state
{"state":"MERGED"}
PS C:\work> gh pr view 2 --repo mmmphyun/git-collaboration-practice --json state
{"state":"MERGED"}
```

### [6단계] 양쪽 로컬 폴더에서 최신 main 동기화 (git pull)
민수와 지윤 폴더의 `main`에서 각각 `git pull`을 수행하여 서로의 작업 파일(`minsu.md`, `jiyun.md`)이 양쪽에 모두 온전히 반영되었음을 확인했습니다.

- **민수 폴더**:
```text
PS C:\work\git-practice-minsu> git checkout main
PS C:\work\git-practice-minsu> git pull origin main
Updating 186a151..fa058bb
Fast-forward
 jiyun.md | 3 +++
 minsu.md | 5 +++++
 2 files changed, 8 insertions(+)
 create mode 100644 jiyun.md
 create mode 100644 minsu.md

PS C:\work\git-practice-minsu> Get-ChildItem
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---        2026-10-08  오후 3:09             86 jiyun.md
-a---        2026-10-08  오후 3:09            152 minsu.md
-a---        2026-10-08  오후 3:07             30 README.md
```

- **지윤 폴더**:
```text
PS C:\work\git-practice-jiyun> git checkout main
PS C:\work\git-practice-jiyun> git pull origin main
Updating 186a151..fa058bb
Fast-forward
 jiyun.md | 3 +++
 minsu.md | 5 +++++
 2 files changed, 8 insertions(+)
 create mode 100644 jiyun.md
 create mode 100644 minsu.md

PS C:\work\git-practice-jiyun> Get-ChildItem
Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
-a---        2026-10-08  오후 3:09             86 jiyun.md
-a---        2026-10-08  오후 3:09            152 minsu.md
-a---        2026-10-08  오후 3:07             30 README.md
```

### [7단계] 후속 작업 (feature/checklist PR 3차 진행 및 브랜치 정리)
지윤 폴더의 최신 `main`에서 `feature/checklist` 브랜치를 생성하고 `checklist.md`를 추가한 후, PR #3 생성 -> 머지 커밋 병합 -> 양쪽 폴더 pull 동기화 -> 로컬 기능 브랜치 정리를 완료했습니다.

```text
# 지윤 폴더: 새 기능 브랜치 작성 및 푸시
PS C:\work\git-practice-jiyun> git checkout -b feature/checklist
PS C:\work\git-practice-jiyun> git add checklist.md
PS C:\work\git-practice-jiyun> git commit -m "feat: 협업 점검표 checklist.md 추가"
PS C:\work\git-practice-jiyun> git push -u origin feature/checklist

# PR #3 생성 및 머지
gh pr create --repo mmmphyun/git-collaboration-practice --base main --head feature/checklist --title "feat: 협업 점검표 추가"
https://github.com/mmmphyun/git-collaboration-practice/pull/3
gh pr merge 3 --repo mmmphyun/git-collaboration-practice --merge

# 양쪽 main 동기화 및 완료 브랜치 정리
PS C:\work\git-practice-minsu> git checkout main; git pull origin main
Updating fa058bb..10c2754
Fast-forward
 checklist.md | 6 ++++++
 1 file changed, 6 insertions(+)
 create mode 100644 checklist.md
PS C:\work\git-practice-minsu> git branch -d feature/minsu
Deleted branch feature/minsu (was b069d20).

PS C:\work\git-practice-jiyun> git checkout main; git pull origin main
Updating fa058bb..10c2754
Fast-forward
 checklist.md | 6 ++++++
 1 file changed, 6 insertions(+)
 create mode 100644 checklist.md
PS C:\work\git-practice-jiyun> git branch -d feature/jiyun
Deleted branch feature/jiyun (was 5abbee5).
PS C:\work\git-practice-jiyun> git branch -d feature/checklist
Deleted branch feature/checklist (was 72bbc6c).
```

### 최종 커밋 그래프 확인
```text
PS C:\work\git-practice-minsu> git log --oneline --graph -n 10
*   10c2754 Merge pull request #3 from feature/checklist
|\  
| * 72bbc6c feat: 협업 점검표 checklist.md 추가
|/  
*   fa058bb Merge pull request #2 from feature/jiyun
|\  
| * 5abbee5 feat: 지윤 작업 일지 추가
* |   a89444e Merge pull request #1 from feature/minsu
|\ \  
| |/  
|/|   
| * b069d20 docs: 민수 작업 일지 상세 보완
| * 5066a81 feat: 민수 작업 일지 추가
|/  
* 186a151 docs: 초기 README 생성
```

---

## 4. 필수 질문 답변

### Q1. `main`에서 `git merge feature/minsu`를 실행하면 어느 브랜치가 변경을 받는가?
**답변**: 현재 체크아웃되어 있는 대상 브랜치인 **`main` 브랜치**가 변경을 받습니다. Git의 머지 명령은 현재 작업 중인 브랜치(HEAD)를 기준으로 인자로 전달된 브랜치의 커밋 이력을 흡수하여 포인터를 갱신하므로, `feature/minsu` 브랜치는 원본 상태를 유지하고 `main` 브랜치에만 새 커밋 및 변경 파일이 반영됩니다.

### Q2. GitHub에서 PR을 병합한 뒤에도 각 폴더에서 `pull`해야 하는 이유는 무엇인가?
**답변**: GitHub 상의 PR 병합은 원격 저장소(`origin`)의 `main` 브랜치에서만 일어난 서버 측 변경이므로, 각 개발자의 로컬 저장소 `main` 브랜치에는 자동으로 반영되지 않기 때문입니다. 로컬 저장소의 기준점을 최신 상태로 갱신하고 동료가 병합한 최신 변경 사항과의 불일치나 충돌을 방지하려면 로컬의 `main`으로 이동하여 반드시 `git pull origin main`을 실행해야 합니다.
