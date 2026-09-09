-- ==============================================================================
-- MPLAD GUARDIAN — PostGIS Spatial Geometry Schema (002_postgis_geometry.sql)
-- Spatial structures for Real State/UT & District boundaries + Project points
-- CRITICAL: Project coordinates are NULL unless authentic GPS exists in source data.
-- ==============================================================================

-- 1. Enable PostGIS extension if available
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Add spatial point geometry to canonical projects table
-- Nullable by default. Will NOT fabricate coordinates.
DO $$ 
BEGIN 
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name='projects' AND column_name='geom'
    ) THEN
        ALTER TABLE projects ADD COLUMN geom geometry(Point, 4326);
    END IF;
END $$;

-- 3. Create Spatial Boundaries Table for Real State/UT and District Polygons
CREATE TABLE IF NOT EXISTS spatial_boundaries (
    id SERIAL PRIMARY KEY,
    boundary_type TEXT NOT NULL, -- 'STATE' or 'DISTRICT'
    state_name TEXT NOT NULL,
    district_name TEXT,
    state_code TEXT,
    census_code TEXT,
    geom geometry(MultiPolygon, 4326),
    centroid geometry(Point, 4326),
    area_sq_km NUMERIC(12, 2),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 4. Spatial GIST Indexes
CREATE INDEX IF NOT EXISTS idx_projects_geom ON projects USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_spatial_boundaries_geom ON spatial_boundaries USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_spatial_boundaries_type ON spatial_boundaries (boundary_type);
CREATE INDEX IF NOT EXISTS idx_spatial_boundaries_state ON spatial_boundaries (state_name);
CREATE INDEX IF NOT EXISTS idx_spatial_boundaries_district ON spatial_boundaries (district_name);
