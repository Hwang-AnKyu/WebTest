# AICOM 개발 진행 상황

## 프로젝트 개요
- **프로젝트명**: AICOM (아이컴)
- **설명**: 다중 게시판 커뮤니티 서비스
- **기술 스택**: Python 3.13, FastAPI, Supabase, HTMX, Tailwind CSS
- **상태**: 전체 구현 완료

## 완료된 주요 기능
- ✅ **인증 시스템**: JWT 쿠키 기반, CSRF 보호, 비밀번호 정책 (8자+, 문자+숫자 필수)
- ✅ **게시판 시스템**: 다중 게시판, 권한 관리 (all/member/admin)
- ✅ **게시글 CRUD**: Quill.js 에디터, Base64 이미지 (1MB 제한)
- ✅ **댓글 시스템**: 2단계 계층 구조 (댓글-대댓글), 들여쓰기 스타일 적용
- ✅ **검색 기능**: RPC 함수로 OR 검색 지원 (제목+내용 동시 검색)
- ✅ **관리자 기능**: 게시판/사용자 관리
- ✅ **프로필 페이지**: 사용자 정보, 통계, 최근 북마크 표시
- ✅ **북마크 기능**: 게시글 북마크 추가/제거, 북마크 목록 페이지
- ✅ **HTMX 통합**: SPA 경험 제공
- ✅ **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- ✅ **Docker 배포**: Nginx + FastAPI 구성

## 보안 구현
- ✅ **XSS 방어**: bleach 라이브러리로 HTML sanitization
- ✅ **CSRF 보호**: Double Submit Cookie 패턴
- ✅ **Rate Limiting**: Nginx 레벨 구현 (30req/min, 인증 10req/min)
- ✅ **보안 헤더**: CSP, X-Frame-Options, X-Content-Type-Options 등
- ✅ **비밀번호 정책**: 최소 8자, 문자와 숫자 필수
- ✅ **안전한 에러 로깅**: 민감정보 노출 방지

## 데이터베이스 구조
- **users**: 사용자 프로필 (auth.users 참조)
- **boards**: 게시판 정보 (UUID 기반)
- **posts**: 게시글 데이터
- **comments**: 댓글 데이터 (auth.users 직접 참조)
- **bookmarks**: 사용자 북마크 (user_id + post_id 유니크)
- **RPC 함수**:
  - `increment_view_count`: 조회수 원자적 증가
  - `search_posts`: OR 검색 지원 (제목+내용)
  - `count_search_posts`: 검색 결과 카운트

## 초기 데이터
- **게시판**:
  - Announcements (관리자 전용)
  - Newsletter (관리자 전용)
  - Free Board (회원 전용)

## 프로젝트 구조
```
project/
├── app/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── routers/             # API 라우터
│   │   ├── auth.py          # 인증
│   │   ├── boards.py        # 게시판
│   │   ├── posts.py         # 게시글
│   │   ├── comments.py      # 댓글
│   │   ├── search.py        # 검색
│   │   ├── admin.py         # 관리자
│   │   └── profile.py       # 프로필/북마크
│   ├── models/
│   │   └── schemas.py       # Pydantic 스키마
│   ├── services/            # 비즈니스 로직
│   │   ├── auth.py
│   │   ├── board.py
│   │   ├── post.py
│   │   ├── comment.py
│   │   ├── search.py
│   │   ├── bookmark.py
│   │   ├── database.py      # Supabase 연결
│   │   └── utils.py         # 유틸리티
│   ├── templates/           # Jinja2 템플릿
│   │   ├── base.html
│   │   ├── pages/
│   │   └── components/
│   └── static/              # 정적 파일
├── tests/                   # 테스트
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── requirements.txt
└── supabase_schema.sql      # DB 스키마
```

## Docker 구성
- **Nginx**: 80포트, 리버스 프록시, Rate limiting, 보안 헤더
- **FastAPI**: 내부 8000포트, 4 workers
- **환경변수**: .env 파일 사용

### 필수 설정 (최초 1회)

#### 1. Supabase 데이터베이스 스키마 설정
```
1. Supabase 대시보드 접속: https://supabase.com/dashboard/project/yxemmeurskvpocxuickw
2. SQL Editor 메뉴로 이동
3. supabase_schema.sql 파일 내용 복사/붙여넣기
4. Run 버튼 클릭하여 실행
```

이 단계는 테이블, 인덱스, RPC 함수, 초기 데이터를 생성합니다.
- users, boards, posts, comments, bookmarks 테이블
- increment_view_count, search_posts, count_search_posts RPC 함수
- 초기 게시판 3개 (Announcements, Newsletter, Free Board)

#### 2. 이메일 확인 비활성화
```
1. Supabase Dashboard > Authentication > Providers > Email
2. "Confirm email" 옵션 OFF로 설정
```
이 설정이 OFF가 아니면 회원가입 후 로그인 시 "Email not confirmed" 에러 발생.

#### 3. 관리자 계정 설정
초기 관리자 계정으로 회원가입 후, Supabase 대시보드에서 is_admin을 TRUE로 설정:
```sql
UPDATE users SET is_admin = TRUE WHERE email = 'your-admin-email@example.com';
```

### 실행 방법
```bash
# Docker 빌드 및 실행
docker compose up --build -d

# 접속
http://localhost

# 로그 확인
docker compose logs -f web

# 중지
docker compose down
```

## 테스트 현황
- **단위 테스트**: pytest 기반
  - test_auth.py: 인증 테스트
  - test_boards.py: 게시판 테스트
  - test_posts.py: 게시글 테스트
  - test_comments.py: 댓글 테스트
  - test_search.py: 검색 테스트
  - test_utils.py: 유틸리티 테스트

- **E2E 테스트 결과** (2026-01-18):
  - ✅ 메인 페이지: 200 OK, 게시판 목록 정상 표시
  - ✅ 게시판 페이지: 200 OK (announcements, newsletter, free-board)
  - ✅ 검색 페이지: 200 OK (빈 검색, 쿼리 검색, 타입별 검색)
  - ✅ 회원가입: 303 Redirect (성공)
  - ⚠️ 로그인: 이메일 확인 필요 (Supabase 설정 변경 필요)
  - ✅ 관리자 페이지: 401 Unauthorized (비로그인 시 정상 동작)
  - ✅ 프로필/북마크: 303 Redirect (비로그인 시 로그인 페이지로 이동)

## 해결된 이전 제한사항
1. ✅ **검색 기능**: RPC 함수로 OR 검색 구현 완료
2. ✅ **댓글 UI**: CSS로 대댓글 들여쓰기 스타일 적용
3. ✅ **프로필 페이지**: 구현 완료
4. ✅ **북마크 기능**: 구현 완료
5. ✅ **비밀번호 정책**: 8자 이상, 문자+숫자 필수 정책 적용

## API 엔드포인트 CSRF 보호
모든 state-changing 엔드포인트에 CSRF 토큰 검증 적용:

### posts.py
- POST `/boards/{board_id}/posts` - 게시글 작성
- PUT `/posts/{post_id}` - 게시글 수정
- DELETE `/posts/{post_id}` - 게시글 삭제
- PATCH `/posts/{post_id}/pin` - 게시글 고정/해제

### comments.py
- POST `/posts/{post_id}/comments` - 댓글 작성
- PUT `/comments/{comment_id}` - 댓글 수정
- DELETE `/comments/{comment_id}` - 댓글 삭제

### admin.py
- POST `/admin/boards` - 게시판 생성
- PUT `/admin/boards/{board_id}` - 게시판 수정
- DELETE `/admin/boards/{board_id}` - 게시판 삭제
- PUT `/admin/users/{user_id}` - 사용자 권한 수정

### profile.py
- POST `/bookmarks/{post_id}` - 북마크 추가
- DELETE `/bookmarks/{post_id}` - 북마크 제거

## 향후 개선 가능 항목
1. **이메일 알림**: 댓글 알림, 공지사항 알림
2. **2FA 지원**: TOTP 기반 2단계 인증
3. **모니터링**: APM 도구 연동, 로그 수집 시스템
4. **파일 업로드**: Supabase Storage 연동 (현재 Base64 방식)
