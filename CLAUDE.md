# AICOM 커뮤니티 서비스

## 프로젝트 개요
- **서비스명**: AICOM (아이컴) - 다중 게시판 서비스

## 기술 스택 
- **백엔드 & SSR 프론트**  
  - Python 3.13 + FastAPI
  - 템플릿: **Jinja2**  
  - UI: Tailwind CSS 3.4 + **HTMX**(전체 페이지 HTMX 갱신)  
- **인증·DB·파일 저장**: **Supabase**  
  - Auth·Storage·SQL은 Supabase API를 *서버 측(FastAPI)* 에서만 호출
  - **브라우저에는 Supabase JS SDK·키를 포함하지 않음**  
- **배포**: 도커컴포즈 (uvicorn 기반 실행 FastAPI 도커, nginx 도커로 구성)
  - FastAPI에서 정적 파일 직접 서빙
  - 단순 구조 지향 (개발/운영 환경 분리 없음)

## 핵심 문서
- **@ARCHITECTURE.md**: 시스템 구조, DB 스키마, API 명세
- **@PROGRESS.md**: 개발 진행 상황, 완료/미완료 작업 (작업 후 반드시 기억해야할 사항)
- **@DESIGN.md**: UI/UX 디자인 가이드
- **@TESTPLAN.md**: 테스트 전략
- **@TESTDATA.md**: 테스트 데이터

## 공통 작업 가이드
- 모든 작업은 ultra think 해서 작업해주세요.
- 모든 작업은 
  1. 먼저 현재 상태를 철저히 분석하고, 
  2. 철저하게 계획을 세우고, 
  3. sub agents 로 분리하지 말고, 순차적인 작업 계획을 작성한 후, 
  4. API 는 모두 TDD 기반으로 테스트 코드 및 실제 코드를 구현하고, 
  5. API 는 예외 케이스까지 완벽히 테스트하고, 
  6. 코드 완성 후에는 바로 종료하지 말고, 전체 코드를 코드 레벨로 확인하여, 확실한 버그가 발견되면, 수정해주세요
- 작업이 완료되면 꼭 기억해야할 내용에 대해서는 PROGRESS.md 파일에 기록해주고, 
- 필요시 CLAUDE.md 와 ARCHITECTURE.md 등의 다음 주요 파일들도 개선해주세요
- 모든 작업은 다음 주요 파일을 확인하여 작업해주세요
  - **@CLAUDE.md**: 전체 프로젝트 개요 및 기술스택과 작업 가이드
  - **@ARCHITECTURE.md**: 시스템 구조, DB 스키마, API 명세
  - **@PROGRESS.md**: 개발 진행 상황, 완료/미완료 작업 (작업 후 반드시 기억해야할 내용)
  - **@DESIGN.md**: UI/UX 디자인 가이드
    - wireframes 하위폴더에 UI 구현이 필요한 모든 화면은 xml 포멧으로 UI 화면 표현
  - **@TESTPLAN.md**: 테스트 항목
  - **@TESTDATA.md**: 테스트시 필요한 데이터
  - **@NOTE.md**: 빈번한 실수와 해결 방법 기억
- 작업 완료 후에는 테스트 항목을 @TESTPLAN.md 파일에 작성하고, 직접 docker 를 실행하고, puppeteer MCP 로 테스트하여, 모든 버그를 side effect 를 고려하여 신중하게 수정한 후, @TESTPLAN.md 에 기재된 모든 테스트 항목이 PASS 할 때까지 작업을 반복합니다
  - 주로 실수하는 항목은 @NOTE.md 파일에 이후 실수를 반복하지 않기 위해 기재합니다.

## MCP 사용 설정
- 다음 MCP 가 연결되어 있으므로, 관련 작업은 해당 MCP 를 직접 사용해서 작업해주세요
  - supabase MCP (supabase 제어)
  - puppeteer MCP (브라우저 제어)

## Supabase 설정
- **프로젝트 ID**: yxemmeurskvpocxuickw
- **초기 관리자**: onlycpp@naver.com / admin123
- **중요**: Email confirmation OFF, RLS OFF
  - FastAPI 내부에서만 supabase 에 엑세스하므로 RLS 불필요

## 주요 기능
1. **게시판**: 다중 게시판, 권한 관리 (all/member/admin)
2. **인증**: JWT 쿠키 방식 (Supabase 기본 설정), CSRF 보호
3. **게시글**: Quill.js 에디터, Base64 이미지 (전체 게시글 1MB 제한)
   - 조회수: 중복 조회 허용 (매번 증가)
4. **댓글**: 2단계 계층 (댓글-대댓글), HTMX 실시간 업데이트
5. **관리자**: 게시판/사용자 관리, 모든 게시글/댓글 수정/삭제 권한
6. **검색**: 전체 또는 특정 게시판 내 제목/내용 검색

## 필수 환경변수 (.env)
```
SUPABASE_URL=https://yxemmeurskvpocxuickw.supabase.co
SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4ZW1tZXVyc2t2cG9jeHVpY2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njg2MzUzNTksImV4cCI6MjA4NDIxMTM1OX0.40n_2r-vX-6qHAXdD_ZUfunmx0ZfG7UFF9zzJi7Nz0g"
SUPABASE_JWT_SECRET="mzsEeM+r3VAV1yUId4iFyxOOAKpC2wcku+Sze9Sq9oKw5aSh9uNr48i/KWJboCLCBJ3C8Qvs6ZMOd2ts3NacQQ=="
SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inl4ZW1tZXVyc2t2cG9jeHVpY2t3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODYzNTM1OSwiZXhwIjoyMDg0MjExMzU5fQ.UDhXTzyHOB9_By3dY8h3wWuRDHmouorHrE72xI-3E_Y"
SESSION_SECRET=test-session-key
COOKIE_SECURE=False
COOKIE_SAMESITE=lax
```

## 보안 체크리스트
- XSS 방어 (bleach) ✅ 구현완료
- CSRF 보호 (Double Submit Cookie) ✅ 구현완료
- Rate Limiting (Nginx) ✅ 구현완료
- HttpOnly·Secure 쿠키 ✅ 구현완료
- 보안 헤더 (CSP, X-Frame-Options 등) ✅ 구현완료
- 에러 로깅 보안 (민감정보 노출 방지) ✅ 구현완료

## 초기 데이터 셋업
- 초기 게시판: 공지사항(관리자만 글쓰기 허용), 뉴스레터(관리자만 글쓰기 허용), 자유게시판(로그인 사용자 모두 글쓰기 허용)

## 프로젝트 완료 상태
- Phase 1-10 모든 개발 단계 완료
- E2E 테스트 시나리오 1-5 완료
- 반응형 디자인 검증 완료 (모바일/태블릿/데스크톱)
- 보안 취약점 점검 및 코드 레벨 검토 완료
- 모든 문서 업데이트 완료
- 데이터베이스 마이그레이션 완료
- 최종 버그 수정 완료

## 환경변수 추가 옵션
```
# CORS 허용 도메인 (쉼표로 구분, 기본값: localhost 도메인들)
ALLOWED_ORIGINS=http://localhost:8000,http://localhost:8001
```