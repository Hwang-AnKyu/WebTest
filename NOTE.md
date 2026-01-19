## 빈번한 실수와 해결 방법

### 1. 빈 문자열 검증
- **실수**: 모델 필드에 min_length 검증 누락
- **해결**: 모든 필수 문자열 필드에 min_length=1 추가
- **예시**: `title: str = Field(..., min_length=1, max_length=255)`

### 2. Race Condition
- **실수**: 조회수 증가 시 read-modify-write 패턴 사용
- **해결**: PostgreSQL RPC 함수로 원자적 연산 구현
- **예시**: `supabase.rpc("increment_post_view_count", {"post_id": post_id})`

### 3. is_active 필터링
- **실수**: 삭제된 항목(is_active=False) 필터링 누락
- **해결**: 모든 조회 쿼리에 `.eq("is_active", True)` 추가
- **주의**: get_board_by_id 같은 단일 조회에서도 체크 필요

### 4. None 값 처리
- **실수**: dict.get() 결과를 템플릿에서 직접 접근
- **해결**: 기본값 제공으로 안전한 접근 보장
- **예시**: `users_dict.get(user_id, {"username": "Unknown User"})`

### 5. Timezone 일관성
- **실수**: datetime.now() 사용 (timezone 없음)
- **해결**: 항상 `datetime.now(timezone.utc)` 사용
- **주의**: 모든 시간 관련 연산에서 UTC 사용

### Pydantic v2 호환성 문제
1. **Field 검증자 변경**
   - 잘못된 코드: `Field(..., regex="^pattern$")`
   - 올바른 코드: `Field(..., pattern="^pattern$")`

2. **Validator 데코레이터 변경**
   - 잘못된 코드: `@validator('field_name')`
   - 올바른 코드: `@field_validator('field_name')`

3. **Config 클래스 변경**
   - 잘못된 코드:
     ```python
     class Config:
         from_attributes = True
     ```
   - 올바른 코드:
     ```python
     model_config = ConfigDict(from_attributes=True)
     ```

### datetime 관련 문제
- 잘못된 코드: `datetime.utcnow()`
- 올바른 코드: `datetime.now(timezone.utc)`

### pytest-asyncio 테스트 문제
1. **AsyncClient 사용**
   - 반드시 ASGITransport 사용: `AsyncClient(transport=ASGITransport(app=app))`
   - fixture로 client 전달 시 async generator 문제 발생 가능

2. **UUID 테스트 데이터**
   - 테스트에서 UUID 필드는 반드시 유효한 UUID 형식 사용
   - 예: `str(uuid.uuid4())` 또는 `"550e8400-e29b-41d4-a716-446655440000"`

### Supabase 모킹
- conftest.py에서 app.database 모듈을 미리 모킹해야 import 오류 방지
- JWT 형식의 키 사용 필요: `"[JWT_FORMAT_KEY]"`

### Mock 체인 설정
1. **복잡한 메서드 체인**
   - Supabase 쿼리 체인을 정확히 모킹해야 함
   - 예: `.table().select().eq().single().execute()`
   - side_effect 사용하여 순차적으로 다른 결과 반환

2. **AsyncMock 사용**
   - async 함수 모킹 시 AsyncMock 필수
   - 예: `BoardService.check_user_permission = AsyncMock(return_value=True)`

### Pydantic 스키마 검증
1. **ResponseValidationError 해결**
   - Mock 데이터에 모든 필수 필드 포함 필요
   - 특히 created_at, updated_at 같은 시간 필드 누락 주의
   - author 객체 포함 시 UserResponse의 모든 필드 필요

2. **URL 파라미터 vs 스키마 필드**
   - URL 파라미터로 전달되는 필드는 스키마에서 제외
   - 예: CommentCreate에서 post_id 제거 (URL: /posts/{post_id}/comments)

### 댓글 시스템 특수 사항
1. **사용자 정보 조회**
   - auth.users (Supabase Auth 테이블): email, id
   - public.users (커스텀 테이블): username, is_admin
   - 두 테이블을 병합하여 완전한 사용자 정보 구성

2. **계층 구조 검증**
   - 대댓글의 대댓글 방지 (parent_id가 있는 댓글의 parent_id 확인)
   - 삭제된 댓글에 대댓글 불가 (is_active 확인)

3. **Mock 데이터 구성**
   - comments 테이블의 user_id는 auth.users 참조 (public.users 아님)
   - 계층적 댓글 조회 시 replies 배열 초기화 필수

### FastAPI Query 파라미터
1. **regex → pattern 변경 (Pydantic v2)**
   - 잘못된 코드: `Query("all", regex="^(title|content|all)$")`
   - 올바른 코드: `Query("all", pattern="^(title|content|all)$")`

### 검색 기능 구현
1. **Supabase 검색 쿼리**
   - 대소문자 구분 없는 검색: `ilike()` 사용
   - 여러 필드 OR 검색: `or_(f"field1.ilike.{term},field2.ilike.{term}")`
   - 와일드카드 추가: `search_term = f"%{query}%"`

2. **Count 쿼리 Mock 설정**
   - 데이터 쿼리와 count 쿼리는 별도로 실행됨
   - `select("*", count="exact")` 형식 사용
   - Mock 설정 시 side_effect로 순차적 반환:
     ```python
     mock_supabase.table.return_value.select.side_effect = [
         data_query_mock,  # 첫 번째: 데이터 조회
         count_query_mock  # 두 번째: 카운트 조회
     ]
     ```

3. **페이지네이션 계산**
   - Supabase range는 inclusive: `limit = per_page - 1`
   - 전체 페이지: `math.ceil(total_count / per_page)`
   - 결과 없을 때: `total_pages = 0`

### 서비스 레이어 패턴
1. **Mock 패치 위치 변경**
   - 서비스 레이어로 리팩토링 후 mock 패치 경로 수정 필요
   - 잘못된 코드: `patch('app.routers.admin.supabase')`
   - 올바른 코드: `patch('app.services.admin.supabase')`

2. **다중 테이블 Mock 설정**
   - 하나의 메서드에서 여러 테이블 접근 시 side_effect 사용
   - 예: BoardService.delete_board에서 boards와 posts 테이블 각각 접근
   ```python
   def table_side_effect(table_name):
       if table_name == "boards":
           return boards_table_mock
       elif table_name == "posts":
           return posts_table_mock
       return MagicMock()
   
   mock_supabase.table.side_effect = table_side_effect
   ```

### Supabase Key 사용 구분
1. **Anon Key 사용 (anon_supabase)**
   - 사용자 인증 작업: sign_up, sign_in_with_password, sign_out
   - 브라우저에서 직접 호출되는 경우 (현재 프로젝트에서는 없음)

2. **Service Role Key 사용 (supabase)**
   - 모든 데이터베이스 작업: table() 쿼리
   - 관리자 작업: 사용자 삭제 등
   - 백엔드에서만 사용 (보안상 중요)

### Docker 포트 충돌 해결
1. **개발 환경 포트 변경**
   - docker-compose.dev.yml에서 포트 변경
   - 8000 → 8001 등 사용 가능한 포트로 변경

2. **프로덕션 환경 포트 변경**
   - docker-compose.yml에서 nginx 포트 변경
   - 80 → 8080 등 사용 가능한 포트로 변경

### 로그인/회원가입 폼 처리 패턴
1. **폼 전송 엔드포인트 분리**
   - API 엔드포인트: JSON 요청 처리 (예: POST /auth/login)
   - 폼 엔드포인트: Form 데이터 처리 (예: POST /auth/login/form)

2. **CSRF 토큰 검증**
   - 폼 데이터에서 csrf_token 추출
   - 쿠키의 csrf_token과 비교
   - 일치하지 않으면 403 에러

3. **에러 처리**
   - 폼 제출 실패 시 동일 페이지로 템플릿 렌더링
   - 성공 시 RedirectResponse로 리다이렉트

### 폼 제출 패턴 (PUT/DELETE 메서드)
1. **HTML 폼 제약사항**
   - HTML 폼은 GET/POST만 지원
   - PUT/DELETE는 JavaScript 또는 별도 처리 필요

2. **해결 방법**
   - POST 메서드 + 별도 폼 핸들러 엔드포인트
   - 예: /posts/{post_id}/form (수정), /posts/{post_id}/delete (삭제)

3. **패턴 예시**
   ```python
   # 폼 핸들러 (POST 메서드)
   @router.post("/posts/{post_id}/form")
   async def update_post_form(
       post_id: str,
       title: str = Form(...),
       content: str = Form(...),
       csrf_token: str = Form(...),
       ...
   ):
       # CSRF 검증
       # 비즈니스 로직 처리
       # 리다이렉트
   ```

### Pydantic Field 명명 규칙
1. **언더스코어 제약**
   - 필드명은 언더스코어로 시작할 수 없음
   - 에러: `NameError: Fields must not use names with leading underscores`

2. **해결 방법**
   - `_method` → `method`
   - HTML hidden field로 사용 시 주의

### HTMX 요청 처리
1. **문제 상황**
   - HTMX 요청 시 Accept 헤더가 없어 JSON 응답 반환
   - 페이지 전환이 제대로 작동하지 않음

2. **해결 방법**
   - HX-Request 헤더도 함께 확인
   ```python
   accept_header = request.headers.get("accept", "")
   hx_request = request.headers.get("hx-request", "")
   
   if "text/html" in accept_header or hx_request:
       return templates.TemplateResponse(...)
   ```

### base.html 필수 JavaScript 함수
1. **공통 함수들**
   - `getCookie()`: 쿠키 값 가져오기
   - `showToast()`: 토스트 메시지 표시
   - `handleFormSubmit()`: 폼 제출 처리
   - `initQuillEditor()`: Quill 에디터 초기화

2. **HTMX 설정**
   - CSRF 토큰 자동 포함
   - 로딩 인디케이터 표시

### 삭제 후 리다이렉트
1. **문제**
   - 삭제 후 board_id를 가져올 수 없음
   - 404 에러 또는 잘못된 페이지로 이동

2. **해결**
   ```python
   # 삭제 전에 게시글 정보 가져오기
   post = await PostService.get_post_by_id(post_id, current_user)
   board_id = post.get("board_id") if post else None
   
   # 게시글 삭제
   result = await PostService.delete_post(post_id, current_user)
   
   # 적절한 페이지로 리다이렉트
   if board_id:
       return RedirectResponse(url=f"/boards/{board_id}", status_code=303)
   ```

### Docker 재시작 시 주의사항
1. **코드 변경 후 재시작 필요**
   - 개발 환경에서도 일부 변경사항은 자동 리로드 안됨
   - docker-compose down && docker-compose up 필요

2. **Health check 확인**
   - 컨테이너 상태가 (healthy)가 될 때까지 대기
   - 로그 확인으로 시작 오류 체크

### 댓글 시스템 폼 처리
1. **폼 핸들러 필요**
   - 댓글도 auth/posts와 동일하게 별도 폼 핸들러 필요
   - /posts/{post_id}/comments/form - 댓글 작성
   - /comments/{comment_id}/form - 댓글 수정
   - /comments/{comment_id}/delete - 댓글 삭제

2. **HTMX 응답 처리**
   - 댓글 작성/수정 시 comment-item.html 템플릿 반환
   - 삭제 시 빈 문자열 반환 (요소 제거)

3. **템플릿 구조**
   - post-detail.html: 전체 댓글 리스트
   - comment-item.html: 개별 댓글 HTML 조각 (HTMX용)

### 댓글 계층 구조 개선 필요
1. **시각적 구분 부족**
   - 대댓글이 들여쓰기 되지 않음
   - CSS 클래스는 있으나 (comment-reply) 스타일 미적용

2. **데이터 구조**
   - CommentService.get_post_comments()가 평면적으로 반환
   - 계층적 구조로 변환 필요

### 검색 기능 (Search) - 해결됨 ✅
1. **Supabase Python Client OR 쿼리 제한**
   - 문제: Supabase Python 클라이언트 v2.1.0에서 `or_()` 메서드 미지원
   - **해결 방법**: PostgreSQL RPC 함수로 서버 사이드 OR 검색 구현
   - RPC 함수들:
     - `search_posts`: 제목+내용 OR 검색
     - `count_search_posts`: 검색 결과 카운트
   - 사용 예:
     ```python
     response = supabase.rpc("search_posts", {
         "search_term": "검색어",
         "search_type": "all",  # 'all', 'title', 'content'
         "board_uuid": None,     # 특정 게시판 필터
         "result_limit": 20,
         "result_offset": 0
     }).execute()
     ```

### Puppeteer MCP 타임아웃 문제
1. **타임아웃 에러 증상**
   - Runtime.evaluate timed out
   - Runtime.callFunctionOn timed out
   - Input.dispatchMouseEvent timed out
   - 긴 페이지 로드나 복잡한 JavaScript 실행 시 발생
   
2. **발생 상황**
   - E2E 시나리오 5 테스트 중 버튼 클릭 시도
   - 복잡한 JavaScript 코드 실행 시
   
3. **해결 방법**
   - Puppeteer MCP 사용 중단
   - 대체 테스트 방법 사용 (수동 테스트, API 직접 호출 등)

### XSS 방어 구현
1. **HTML Sanitization 필수**
   - 사용자 입력 HTML은 반드시 bleach로 sanitize
   - 게시글 content: sanitize_html() 사용 (Quill.js 호환 태그만 허용)
   - 제목, 댓글, 게시판 정보: sanitize_text() 사용 (모든 HTML 제거)
   - 템플릿에서 `| safe` 필터 사용 시 반드시 사전 sanitization 확인

2. **Sanitization 위치**
   - 서비스 레이어에서 데이터 저장 전 수행
   - create와 update 모두에서 수행
   - 절대 클라이언트 측 sanitization에만 의존하지 않음

### CSRF 보호
1. **CSRF 제외 경로 최소화**
   - 오직 /auth/login, /auth/signup, /auth/refresh만 제외
   - /auth/logout은 반드시 CSRF 보호 필요 (상태 변경)
   
2. **Form 엔드포인트 패턴**
   - 모든 폼 제출 엔드포인트는 CSRF 토큰 검증 필수
   - 미들웨어에서 자동 검증되므로 개별 검증 불필요

### 에러 로깅 패턴
1. **민감정보 노출 방지**
   - 잘못된 예: `logger.error(f"Failed: {str(e)}")`
   - 올바른 예: `logger.error("Failed", exc_info=True)`
   - exc_info=True는 스택 트레이스를 로그 파일에만 기록

### 보안 헤더
1. **CSP (Content Security Policy)**
   - CDN 리소스 명시적 허용 필요
   - Quill.js는 'unsafe-inline' 필요 (에디터 동작)
   - 새 CDN 추가 시 CSP 업데이트 필수

### 데이터베이스 초기 설정 필수
1. **테이블 및 RPC 함수 생성 필요**
   - 애플리케이션 실행 전 supabase_schema.sql 실행 필수
   - Supabase 대시보드 SQL Editor에서 직접 실행
   - 테이블: users, boards, posts, comments, bookmarks
   - RPC 함수: increment_view_count, search_posts, count_search_posts

2. **초기 데이터**
   - 스키마 SQL에 초기 게시판 3개 자동 생성 포함
   - 관리자 계정은 회원가입 후 is_admin = TRUE로 수동 설정

3. **.env 파일 형식 주의**
   - 등호(=) 뒤에 공백 없이 작성
   - 잘못된 예: `SUPABASE_ANON_KEY= "value"`
   - 올바른 예: `SUPABASE_ANON_KEY=value`

### 이메일 확인 설정 필수
1. **Supabase 설정**
   - Authentication > Providers > Email에서 "Confirm email" 설정 OFF 필요
   - 그렇지 않으면 회원가입 후 로그인 불가 (Email not confirmed 에러)

2. **기존 사용자 이메일 확인**
   - 이메일 확인이 활성화된 상태에서 가입한 사용자는 수동 확인 필요
   - Supabase Dashboard > Authentication > Users에서 확인 처리

### 게시판 URL 구조
1. **UUID와 slug 모두 지원**
   - `/boards/free-board` (slug로 접근)
   - `/boards/{uuid}` (UUID로 접근)
   - `get_board_by_id_or_slug()` 메서드가 자동 판별

### Supabase single() 메서드 예외 처리
1. **문제**
   - `single()` 메서드는 결과가 없을 때 `APIError` (PGRST116) 예외 발생
   - 잘못된 UUID 형식일 때 `APIError` (22P02) 예외 발생
   - 기존 코드에서 500 Internal Server Error 반환

2. **해결**
   ```python
   from postgrest.exceptions import APIError

   try:
       response = supabase.table("posts").select("*").eq("id", post_id).single().execute()
   except APIError as e:
       error_str = str(e)
       # 결과 없음 (PGRST116)
       if "PGRST116" in error_str or "0 rows" in error_str:
           raise HTTPException(status_code=404, detail="Post not found")
       # 잘못된 UUID 형식 (22P02)
       if "22P02" in error_str or "invalid input syntax for type uuid" in error_str:
           raise HTTPException(status_code=404, detail="Post not found")
       raise
   ```
   - `APIError`를 명시적으로 처리하여 404 반환
   - PGRST116: 결과가 0개일 때
   - 22P02: UUID 형식이 잘못되었을 때