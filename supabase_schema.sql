-- AICOM Database Schema
-- Run this SQL in Supabase SQL Editor

-- ==================== Users Table ====================
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== Boards Table ====================
CREATE TABLE IF NOT EXISTS public.boards (
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

-- ==================== Posts Table ====================
CREATE TABLE IF NOT EXISTS public.posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    board_id UUID NOT NULL REFERENCES public.boards(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    view_count INTEGER DEFAULT 0,
    is_pinned BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== Comments Table ====================
CREATE TABLE IF NOT EXISTS public.comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    parent_id UUID REFERENCES public.comments(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ==================== Bookmarks Table ====================
CREATE TABLE IF NOT EXISTS public.bookmarks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    post_id UUID NOT NULL REFERENCES public.posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);

-- ==================== Indexes ====================
CREATE INDEX IF NOT EXISTS idx_posts_board_id ON public.posts(board_id);
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON public.posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON public.posts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_posts_is_active ON public.posts(is_active);
CREATE INDEX IF NOT EXISTS idx_posts_title_search ON public.posts USING gin(to_tsvector('simple', title));
CREATE INDEX IF NOT EXISTS idx_posts_content_search ON public.posts USING gin(to_tsvector('simple', coalesce(content, '')));

CREATE INDEX IF NOT EXISTS idx_comments_post_id ON public.comments(post_id);
CREATE INDEX IF NOT EXISTS idx_comments_user_id ON public.comments(user_id);
CREATE INDEX IF NOT EXISTS idx_comments_parent_id ON public.comments(parent_id);

CREATE INDEX IF NOT EXISTS idx_bookmarks_user_id ON public.bookmarks(user_id);
CREATE INDEX IF NOT EXISTS idx_bookmarks_post_id ON public.bookmarks(post_id);

CREATE INDEX IF NOT EXISTS idx_boards_slug ON public.boards(slug);
CREATE INDEX IF NOT EXISTS idx_boards_display_order ON public.boards(display_order);

-- ==================== RPC Functions ====================

-- Increment view count atomically
CREATE OR REPLACE FUNCTION public.increment_view_count(post_id UUID)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    new_count INTEGER;
BEGIN
    UPDATE public.posts
    SET view_count = view_count + 1
    WHERE id = post_id
    RETURNING view_count INTO new_count;

    RETURN new_count;
END;
$$;

-- Search posts with OR query support (title + content)
CREATE OR REPLACE FUNCTION public.search_posts(
    search_term TEXT,
    search_type TEXT DEFAULT 'all',
    board_uuid UUID DEFAULT NULL,
    result_limit INTEGER DEFAULT 20,
    result_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    board_id UUID,
    user_id UUID,
    title VARCHAR(255),
    content TEXT,
    view_count INTEGER,
    is_pinned BOOLEAN,
    is_active BOOLEAN,
    created_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE
)
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    search_pattern TEXT;
BEGIN
    search_pattern := '%' || search_term || '%';

    RETURN QUERY
    SELECT
        p.id,
        p.board_id,
        p.user_id,
        p.title,
        p.content,
        p.view_count,
        p.is_pinned,
        p.is_active,
        p.created_at,
        p.updated_at
    FROM public.posts p
    WHERE p.is_active = TRUE
        AND (board_uuid IS NULL OR p.board_id = board_uuid)
        AND (
            CASE
                WHEN search_type = 'title' THEN p.title ILIKE search_pattern
                WHEN search_type = 'content' THEN p.content ILIKE search_pattern
                ELSE p.title ILIKE search_pattern OR p.content ILIKE search_pattern
            END
        )
    ORDER BY p.created_at DESC
    LIMIT result_limit
    OFFSET result_offset;
END;
$$;

-- Count search results
CREATE OR REPLACE FUNCTION public.count_search_posts(
    search_term TEXT,
    search_type TEXT DEFAULT 'all',
    board_uuid UUID DEFAULT NULL
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    search_pattern TEXT;
    result_count INTEGER;
BEGIN
    search_pattern := '%' || search_term || '%';

    SELECT COUNT(*)::INTEGER INTO result_count
    FROM public.posts p
    WHERE p.is_active = TRUE
        AND (board_uuid IS NULL OR p.board_id = board_uuid)
        AND (
            CASE
                WHEN search_type = 'title' THEN p.title ILIKE search_pattern
                WHEN search_type = 'content' THEN p.content ILIKE search_pattern
                ELSE p.title ILIKE search_pattern OR p.content ILIKE search_pattern
            END
        );

    RETURN result_count;
END;
$$;

-- ==================== Initial Data ====================

-- Insert initial boards (only if they don't exist)
INSERT INTO public.boards (name, slug, description, icon, can_write, can_read, display_order)
SELECT * FROM (VALUES
    ('Announcements', 'announcements', 'Official announcements and updates', '📢', 'admin', 'all', 1),
    ('Newsletter', 'newsletter', 'Latest news and articles', '📰', 'admin', 'all', 2),
    ('Free Board', 'free-board', 'Share your thoughts freely', '💬', 'member', 'all', 3)
) AS v(name, slug, description, icon, can_write, can_read, display_order)
WHERE NOT EXISTS (SELECT 1 FROM public.boards WHERE slug IN ('announcements', 'newsletter', 'free-board'));

-- Grant permissions
GRANT EXECUTE ON FUNCTION public.increment_view_count TO authenticated;
GRANT EXECUTE ON FUNCTION public.increment_view_count TO service_role;
GRANT EXECUTE ON FUNCTION public.search_posts TO authenticated;
GRANT EXECUTE ON FUNCTION public.search_posts TO service_role;
GRANT EXECUTE ON FUNCTION public.search_posts TO anon;
GRANT EXECUTE ON FUNCTION public.count_search_posts TO authenticated;
GRANT EXECUTE ON FUNCTION public.count_search_posts TO service_role;
GRANT EXECUTE ON FUNCTION public.count_search_posts TO anon;
