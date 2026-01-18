# AICOM 디자인 문서

### 디자인 가이드라인
- 반응형 완벽 지원 (puppeteer MCP 로 반응형 디자인도 문제가 없는지 확인)
- https://tx.shadcn.com/ 스타일로 전체 웹페이지에 일관된 디자인 적용

## XML 디자인 파일 개요

- AICOM 서비스의 모든 페이지 구조를 XML 형식으로 정의합니다. 
- 각 XML 파일은 페이지의 구조와 요소를 명확하게 표현하여 구현 시 참조할 수 있도록 합니다.

## XML 파일 목록

### 1. 공통 컴포넌트
- **@header.xml**: 모든 페이지 공통 헤더
- **@footer.xml**: 모든 페이지 공통 푸터

### 2. 메인 및 인증 페이지
- **@main.xml**: 메인 페이지 (/)
- **@login.xml**: 로그인 페이지 (/auth/login)
- **@signup.xml**: 회원가입 페이지 (/auth/signup)

### 3. 게시판 페이지
- **@board.xml**: 게시판 상세 페이지 (/boards/{board_id})
- **@post-detail.xml**: 게시글 상세 페이지 (/posts/{post_id})
- **@post-create.xml**: 게시글 작성 페이지 (/boards/{board_id}/posts/create)
- **@post-edit.xml**: 게시글 수정 페이지 (/posts/{post_id}/edit)
- **@search.xml**: 검색 페이지 (/search)

### 4. 관리자 페이지
- **@admin.xml**: 관리자 메인 페이지 (/admin)
- **@admin-boards.xml**: 게시판 관리 페이지 (/admin/boards)
- **@admin-users.xml**: 사용자 관리 페이지 (/admin/users)

