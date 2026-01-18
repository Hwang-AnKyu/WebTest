# AICOM 아키텍처 문서

## 페이지 플로우 다이어그램
```
[비로그인 사용자]
├── 메인페이지 (/)
│   └── 게시판 목록 (/boards)
│       └── 게시글 읽기 (/posts/{post_id})
└── 인증
    ├── 로그인 (/auth/login)
    └── 회원가입 (/auth/signup)

[로그인 사용자]
├── 메인페이지 (/)
│   └── 게시판 목록 (/boards/{board_id})
│       ├── 게시글 읽기 (/posts/{post_id})
│       ├── 게시글 작성 (/boards/{board_id}/posts/create)
│       └── 검색 (/search)
├── 게시글 관리
│   ├── 게시글 수정 (/posts/{post_id}/edit)
│   └── 게시글 삭제 (/posts/{post_id}/delete)
├── 댓글 관리
│   ├── 댓글 작성 (POST /posts/{post_id}/comments)
│   ├── 댓글 수정 (/comments/{comment_id}/edit)
│   └── 댓글 삭제 (/comments/{comment_id}/delete)
└── 로그아웃 (/auth/logout)

[관리자]
├── 모든 로그인 사용자 기능
└── 관리자 페이지 (/admin)
    ├── 게시판 관리 (/admin/boards)
    │   ├── 게시판 생성 (POST /admin/boards)
    │   ├── 게시판 수정 (PUT /admin/boards/{board_id})
    │   └── 게시판 삭제 (DELETE /admin/boards/{board_id})
    └── 사용자 관리 (/admin/users)
        └── 권한 수정 (PUT /admin/users/{user_id})
```

## 시스템 구조
```
Docker Compose
├── FastAPI (uvicorn)
│   ├── 정적 파일 서빙
│   ├── API 엔드포인트
│   └── HTMX 응답
└── Nginx
    └── Rate Limiting
```

## 프로젝트 디렉토리 구조
```
project/
├── app/
│   ├── main.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── boards.py
│   │   ├── posts.py
│   │   ├── comments.py
│   │   └── admin.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── auth.py
│   │   ├── database.py
│   │   └── utils.py
│   ├── templates/
│   │   ├── base.html
│   │   ├── components/
│   │   └── pages/
│   └── static/
│       ├── css/
│       └── js/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env
```

## URL 라우팅 체계
```
/ - 메인 페이지 (게시판 목록)
/auth/login - 로그인
/auth/signup - 회원가입
/auth/logout - 로그아웃

/boards - 게시판 목록
/boards/{board_id} - 특정 게시판
/boards/{board_id}/posts/create - 게시글 작성
/posts/{post_id} - 게시글 상세
/posts/{post_id}/edit - 게시글 수정
/posts/{post_id}/delete - 게시글 삭제

/comments/create - 댓글 작성
/comments/{comment_id}/edit - 댓글 수정
/comments/{comment_id}/delete - 댓글 삭제

/admin - 관리자 페이지
/admin/boards - 게시판 관리
/admin/users - 사용자 관리

/search - 검색 (쿼리: board_id, q, type)
```

## UI 디자인 (wireframes/)
### 공통 컴포넌트
- **@header.xml**: 공통 헤더
- **@footer.xml**: 공통 푸터

### 주요 페이지
- **@main.xml**: 메인 페이지
- **@login.xml**: 로그인
- **@signup.xml**: 회원가입
- **@board.xml**: 게시판 상세
- **@post-detail.xml**: 게시글 상세
- **@post-create.xml**: 게시글 작성
- **@post-edit.xml**: 게시글 수정
- **@search.xml**: 검색

### 관리자 페이지
- **@admin.xml**: 관리자 메인
- **@admin-boards.xml**: 게시판 관리
- **@admin-users.xml**: 사용자 관리

## DB 스키마

### users (Supabase Auth 제공)
- id: UUID
- email: String
- created_at: Timestamp

### users (사용자 프로필 - 기존 테이블)
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### boards (게시판 - 기존 테이블)
```sql
CREATE TABLE boards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(255),
    can_write VARCHAR(20) DEFAULT 'member' CHECK (can_write IN ('all', 'member', 'admin')),
    can_read VARCHAR(20) DEFAULT 'all' CHECK (can_read IN ('all', 'member', 'admin')),
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### posts (게시글 - 기존 테이블)
```sql
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES boards(id),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    content TEXT, -- Quill.js HTML + Base64 이미지
    view_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### comments (댓글 - 기존 테이블)
```sql
CREATE TABLE comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES posts(id),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    parent_id UUID REFERENCES comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### RPC Functions (저장 프로시저)
```sql
-- 조회수 증가 함수 (원자적 연산으로 동시성 문제 해결)
CREATE OR REPLACE FUNCTION increment_view_count(post_id UUID)
RETURNS INTEGER AS $$
DECLARE
  new_count INTEGER;
BEGIN
  UPDATE posts 
  SET view_count = view_count + 1
  WHERE id = post_id
  RETURNING view_count INTO new_count;
  
  RETURN new_count;
END;
$$ LANGUAGE plpgsql;

-- 권한 부여
GRANT EXECUTE ON FUNCTION increment_view_count TO authenticated;
```

## 주요 API

### 인증
- POST /auth/signup - 회원가입
- POST /auth/login - 로그인  
- POST /auth/logout - 로그아웃
- GET /auth/me - 현재 사용자 정보

### 게시판
- GET /boards - 게시판 목록
- GET /boards/{board_id} - 게시판 상세 (게시글 목록 포함)
- POST /admin/boards - 게시판 생성 (관리자)
- PUT /admin/boards/{board_id} - 게시판 수정 (관리자)
- DELETE /admin/boards/{board_id} - 게시판 삭제 (관리자)

### 게시글
- GET /posts/{post_id} - 게시글 상세 (조회수 증가)
- POST /boards/{board_id}/posts - 게시글 작성
- PUT /posts/{post_id} - 게시글 수정
- DELETE /posts/{post_id} - 게시글 삭제

### 댓글
- POST /posts/{post_id}/comments - 댓글 작성
- PUT /comments/{comment_id} - 댓글 수정
- DELETE /comments/{comment_id} - 댓글 삭제

### 검색
- GET /search - 통합 검색
  - Query params: q(검색어), board_id(선택), type(title/content)

### 관리자
- GET /admin/users - 사용자 목록
- PUT /admin/users/{user_id} - 사용자 권한 수정

## 기술적 결정사항

### HTMX 구현
- **페이지 전환**: `hx-target="body"` + `hx-push-url="true"`
- **로딩 상태**: `hx-indicator` 활용한 스피너 표시
- **에러 처리**: 응답 헤더에 따른 토스트 메시지

### UI/UX 세부사항
- **권한 기반 버튼 표시**: 서버에서 권한 확인 후 버튼 렌더링
- **댓글 인터페이스**: 인라인 편집/답글 입력창
- **에러 메시지**: 폼 아래 인라인 표시

### Quill 에디터 설정
```javascript
modules: {
  toolbar: [
    ['bold', 'italic', 'underline', 'strike'],
    ['link', 'image'],
    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
    ['clean']
  ]
}
```
- 이미지 붙여넣기/드래그 시 즉시 Base64 변환
- 에디터 내용 변경 시 실시간 크기 검증

### 페이지네이션
- 페이지당 20개 게시글/검색결과
- 페이지 번호 5개씩 표시

### 정적 파일 및 라이브러리
- **CDN 사용** (안정성과 단순성):
  - Tailwind CSS: CDN
  - HTMX: CDN (v1.9.x)
  - Quill.js: CDN (v1.3.x)
- **빌드 프로세스 없음** (복잡도 최소화)

### Docker 구성

통합된 docker-compose.yml로 로컬과 AWS 환경 모두 지원:

#### 환경별 실행 방법
```bash
# 로컬 개발 환경 (포트 8000, 코드 리로드)
./run.sh local up

# 프로덕션 환경 (포트 8000, nginx 없음, CloudFront 사용 시)
./run.sh prod up

# AWS 환경 (포트 8080, nginx 포함, EC2 직접 실행 시)
./run.sh aws up
```

#### docker-compose.yml 구조
```yaml
services:
  web:
    build: .
    ports:
      - "${WEB_PORT:-8000}:8000"
    environment:
      - ENVIRONMENT=${ENVIRONMENT:-production}
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "${RELOAD_FLAG:---workers=4}"]
  
  nginx:
    image: nginx:alpine
    ports:
      - "${NGINX_PORT:-8080}:80"
    profiles:
      - with-nginx  # AWS 환경에서만 활성화
```

#### 배포 시나리오
1. **CloudFront + ALB/ECS**: nginx 없이 FastAPI 직접 서비스 (prod 모드)
2. **CloudFront + EC2**: nginx 포함하여 rate limiting 등 활용 (aws 모드)
3. **로컬 개발**: 코드 리로드 활성화 (local 모드)

### Nginx Rate Limiting
```nginx
limit_req_zone $binary_remote_addr zone=general:10m rate=30r/m;
limit_req zone=general burst=10 nodelay;
```

### 초기 데이터 설정
- Supabase MCP를 통한 직접 데이터 삽입
- 관리자 계정 및 초기 게시판 생성
