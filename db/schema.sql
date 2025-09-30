-- 사용자 테이블
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,       -- 사용자 고유 ID
    userid VARCHAR(50) UNIQUE,                  -- 사이트 전용 로그인 ID (OAuth 아닌 경우)
    email VARCHAR(100) UNIQUE,                  -- 이메일
    pw_hash VARCHAR(255),                        -- bcrypt로 해시된 비밀번호
    name VARCHAR(100),                           -- 사용자 이름
    phonenum VARCHAR(50),                        -- 전화번호
    bthday DATE,                                 -- 생년월일
    gender VARCHAR(10),                           -- 성별
    role VARCHAR(50) DEFAULT 'user',             -- 권한 (user/admin 등)
    
    -- OAuth 관련
    provider VARCHAR(50),                         -- OAuth 제공자 (google, kakao 등)
    provider_id VARCHAR(100),                     -- OAuth 제공자 고유 ID
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);



-- 사용자 프로필 테이블
CREATE TABLE user_profiles (
    user_id BIGINT PRIMARY KEY,
    profile_image_path TEXT,                     -- 프로필 이미지
    bio TEXT,                                    -- 자기소개
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_user_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);



-- 지역
CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE,                     -- 행정/법정동 코드
    name VARCHAR(100) NOT NULL,                  -- 지역명 (예: 서울특별시, 강남구)
    parent_id INT,                               -- 상위 지역 참조
    level INT,                                   -- 행정 레벨
    CONSTRAINT fk_regions_parent FOREIGN KEY (parent_id) REFERENCES regions(id) ON DELETE SET NULL
);



-- 카테고리
CREATE TABLE categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    code VARCHAR(50) UNIQUE,
    name VARCHAR(100) NOT NULL,
    parent_id INT,
    sort_order INT DEFAULT 0,
    CONSTRAINT fk_categories_parent FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);



-- 관광지
CREATE TABLE places (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source VARCHAR(50) NOT NULL,                 -- 데이터 출처 (tourapi/manual)
    source_id VARCHAR(100),                      -- 외부 시스템 ID
    title VARCHAR(300) NOT NULL,
    slug VARCHAR(300) UNIQUE,                    -- SEO용 slug
    short_desc TEXT,
    description TEXT,
    category_id INT,
    region_id INT,
    address VARCHAR(500),
    postcode VARCHAR(20),
    phone VARCHAR(50),
    website VARCHAR(500),
    latitude DECIMAL(10,7),
    longitude DECIMAL(10,7),
    avg_rating DECIMAL(3,2) DEFAULT 0,
    review_count INT DEFAULT 0,
    images_count INT DEFAULT 0,
    is_public BOOLEAN DEFAULT TRUE,
    meta JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_places_category FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL,
    CONSTRAINT fk_places_region FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL
);



-- 관광지 상세
CREATE TABLE place_details (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    place_id BIGINT NOT NULL UNIQUE,             -- 1:1 관계
    opening_hours VARCHAR(200),
    closed_days VARCHAR(200),
    admission_fee VARCHAR(200),
    parking_info VARCHAR(200),
    facilities JSON,
    transport_info TEXT,
    accessibility JSON,
    avg_rating DECIMAL(3,2) DEFAULT 0,
    review_count INT DEFAULT 0,
    is_restaurant BOOLEAN DEFAULT FALSE,
    signature_menu VARCHAR(200),                 -- 대표 메뉴 (선택 사항)
    menu_items JSON,                             -- 취급 메뉴 (선택 사항)
    video_url VARCHAR(500),
    official_site VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_place_details_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 축제
CREATE TABLE festivals (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    place_id BIGINT,
    region_id INT,
    start_date DATE,
    end_date DATE,
    organizer VARCHAR(200),
    price VARCHAR(100),
    description TEXT,
    contact VARCHAR(100),
    images_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_festivals_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE SET NULL,
    CONSTRAINT fk_festivals_region FOREIGN KEY (region_id) REFERENCES regions(id) ON DELETE SET NULL
);



-- 여행코스
CREATE TABLE itineraries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    description TEXT,
    duration_days INT,
    created_by BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_itineraries_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE itinerary_items (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    itinerary_id BIGINT NOT NULL,
    seq INT NOT NULL,                            -- 순서
    place_id BIGINT,
    note TEXT,
    est_minutes INT,
    CONSTRAINT fk_itinerary_items_itinerary FOREIGN KEY (itinerary_id) REFERENCES itineraries(id) ON DELETE CASCADE,
    CONSTRAINT fk_itinerary_items_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE SET NULL
);



-- 이미지
CREATE TABLE images (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    place_id BIGINT,
    category VARCHAR(50),                        -- 관광지, 축제, 코스 등
    file_path TEXT NOT NULL,                      -- Docker 볼륨 경로
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_images_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 날씨
CREATE TABLE weather_avg_5y (
    stat_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    place_id BIGINT NOT NULL,
    month TINYINT NOT NULL,
    day TINYINT NOT NULL,
    avg_temperature FLOAT NOT NULL,
    avg_precipitation FLOAT,
    avg_humidity FLOAT,
    dominant_condition VARCHAR(50),
    CONSTRAINT fk_weather_avg_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);

CREATE TABLE weather_current (
    weather_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    place_id BIGINT NOT NULL,
    weather_date DATE NOT NULL,
    temperature FLOAT NOT NULL,
    precipitation FLOAT,
    humidity FLOAT,
    `condition` VARCHAR(50),
    CONSTRAINT fk_weather_current_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 즐겨찾기
CREATE TABLE favorites (
    user_id BIGINT NOT NULL,
    place_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, place_id),
    CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_favorites_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 리뷰
CREATE TABLE reviews (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    place_id BIGINT,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(200),
    content TEXT,
    is_public BOOLEAN DEFAULT TRUE,
    likes INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_reviews_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 조회수
CREATE TABLE place_views_daily (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    place_id BIGINT,
    view_date DATE,
    view_count INT DEFAULT 0,
    CONSTRAINT fk_place_views_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);

CREATE TABLE place_stats (
    place_id BIGINT PRIMARY KEY,
    total_views INT DEFAULT 0,
    total_likes INT DEFAULT 0,
    CONSTRAINT fk_place_stats_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE
);



-- 캘린더
CREATE TABLE user_calendar (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    place_id BIGINT,
    event_date DATE NOT NULL,
    memo VARCHAR(255),
    CONSTRAINT fk_calendar_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_calendar_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE SET NULL
);



-- 태크
CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    slug VARCHAR(100) UNIQUE
);

CREATE TABLE place_tags (
    place_id BIGINT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY(place_id, tag_id),
    CONSTRAINT fk_place_tags_place FOREIGN KEY (place_id) REFERENCES places(id) ON DELETE CASCADE,
    CONSTRAINT fk_place_tags_tag FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

