/*
  # AutoLight Analyser Database Schema

  ## Overview
  This migration creates the complete database schema for the AutoLight Analyser application,
  which processes CAD files to detect lighting fixtures and provide cost analysis.

  ## New Tables
  
  ### 1. `projects`
  Stores uploaded CAD file projects and their metadata
  - `id` (uuid, primary key) - Unique project identifier
  - `name` (text) - Project name
  - `file_name` (text) - Original uploaded file name
  - `file_type` (text) - File extension (dwg/dxf)
  - `upload_date` (timestamptz) - When project was uploaded
  - `total_fixtures` (integer) - Count of detected fixtures
  - `total_cost` (numeric) - Total project cost
  - `average_lux` (numeric) - Average lux level across all rooms
  - `user_id` (uuid) - Reference to auth.users
  - `created_at` (timestamptz) - Record creation timestamp

  ### 2. `fixture_models`
  Catalog of available lighting fixture models with specifications
  - `id` (uuid, primary key) - Unique model identifier
  - `model_name` (text) - Model name/number
  - `manufacturer` (text) - Manufacturer name
  - `fixture_type` (text) - Type (LED, Fluorescent, etc.)
  - `wattage` (numeric) - Power consumption in watts
  - `lumens` (numeric) - Light output in lumens
  - `unit_price` (numeric) - Price per unit
  - `description` (text) - Model description
  - `created_at` (timestamptz) - Record creation timestamp

  ### 3. `fixtures`
  Detected fixtures in each project
  - `id` (uuid, primary key) - Unique fixture identifier
  - `project_id` (uuid, foreign key) - Reference to projects table
  - `room_name` (text) - Room where fixture is located
  - `detected_symbol` (text) - Symbol detected in CAD file
  - `selected_model_id` (uuid, foreign key) - Currently selected fixture model
  - `quantity` (integer) - Number of this fixture type
  - `lux_level` (numeric) - Calculated lux level
  - `created_at` (timestamptz) - Record creation timestamp

  ### 4. `fixture_recommendations`
  Alternative fixture recommendations for each detected fixture
  - `id` (uuid, primary key) - Unique recommendation identifier
  - `fixture_id` (uuid, foreign key) - Reference to fixtures table
  - `recommended_model_id` (uuid, foreign key) - Reference to fixture_models
  - `reason` (text) - Recommendation reason
  - `priority` (integer) - Recommendation priority (1=highest)
  - `created_at` (timestamptz) - Record creation timestamp

  ## Security
  - Enable RLS on all tables
  - Add policies for authenticated users to manage their own projects
  - Public read access to fixture_models catalog
*/

-- Create projects table
CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  file_name text NOT NULL,
  file_type text NOT NULL,
  upload_date timestamptz DEFAULT now(),
  total_fixtures integer DEFAULT 0,
  total_cost numeric(10,2) DEFAULT 0,
  average_lux numeric(10,2) DEFAULT 0,
  user_id uuid REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now()
);

-- Create fixture_models table
CREATE TABLE IF NOT EXISTS fixture_models (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  model_name text NOT NULL,
  manufacturer text NOT NULL,
  fixture_type text NOT NULL,
  wattage numeric(10,2) NOT NULL,
  lumens numeric(10,2) NOT NULL,
  unit_price numeric(10,2) NOT NULL,
  description text DEFAULT '',
  created_at timestamptz DEFAULT now()
);

-- Create fixtures table
CREATE TABLE IF NOT EXISTS fixtures (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid REFERENCES projects(id) ON DELETE CASCADE NOT NULL,
  room_name text NOT NULL,
  detected_symbol text NOT NULL,
  selected_model_id uuid REFERENCES fixture_models(id),
  quantity integer DEFAULT 1,
  lux_level numeric(10,2) DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

-- Create fixture_recommendations table
CREATE TABLE IF NOT EXISTS fixture_recommendations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  fixture_id uuid REFERENCES fixtures(id) ON DELETE CASCADE NOT NULL,
  recommended_model_id uuid REFERENCES fixture_models(id) NOT NULL,
  reason text DEFAULT '',
  priority integer DEFAULT 1,
  created_at timestamptz DEFAULT now()
);

-- Enable RLS
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_models ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixture_recommendations ENABLE ROW LEVEL SECURITY;

-- Projects policies
CREATE POLICY "Users can view own projects"
  ON projects FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users can create own projects"
  ON projects FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own projects"
  ON projects FOR UPDATE
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects"
  ON projects FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Fixture models policies (public read, admin write)
CREATE POLICY "Anyone can view fixture models"
  ON fixture_models FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Authenticated users can create fixture models"
  ON fixture_models FOR INSERT
  TO authenticated
  WITH CHECK (true);

-- Fixtures policies
CREATE POLICY "Users can view fixtures from own projects"
  ON fixtures FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = fixtures.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create fixtures in own projects"
  ON fixtures FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = fixtures.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can update fixtures in own projects"
  ON fixtures FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = fixtures.project_id
      AND projects.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = fixtures.project_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete fixtures from own projects"
  ON fixtures FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      WHERE projects.id = fixtures.project_id
      AND projects.user_id = auth.uid()
    )
  );

-- Fixture recommendations policies
CREATE POLICY "Users can view recommendations for own project fixtures"
  ON fixture_recommendations FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM fixtures
      JOIN projects ON projects.id = fixtures.project_id
      WHERE fixtures.id = fixture_recommendations.fixture_id
      AND projects.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can create recommendations for own project fixtures"
  ON fixture_recommendations FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM fixtures
      JOIN projects ON projects.id = fixtures.project_id
      WHERE fixtures.id = fixture_recommendations.fixture_id
      AND projects.user_id = auth.uid()
    )
  );

-- Insert sample fixture models
INSERT INTO fixture_models (model_name, manufacturer, fixture_type, wattage, lumens, unit_price, description)
VALUES
  ('LED-P600-40W', 'BrightLite', 'LED Panel', 40, 4000, 45.99, '600x600mm LED panel, 4000K, high efficiency'),
  ('LED-P600-36W', 'EcoLight', 'LED Panel', 36, 3800, 42.50, '600x600mm LED panel, energy saving'),
  ('FL-T8-36W', 'StandardCorp', 'Fluorescent', 36, 2800, 12.99, 'T8 fluorescent tube, standard output'),
  ('LED-DL-12W', 'ModernLux', 'LED Downlight', 12, 1200, 18.75, 'Recessed LED downlight, 3000K warm white'),
  ('LED-DL-15W', 'BrightLite', 'LED Downlight', 15, 1500, 22.50, 'Recessed LED downlight, adjustable'),
  ('LED-STRIP-14W', 'FlexLight', 'LED Strip', 14, 1400, 28.00, '5m LED strip, dimmable, warm white'),
  ('LED-HB-100W', 'IndustrialPro', 'LED High Bay', 100, 13000, 125.00, 'Industrial high bay, 5000K daylight'),
  ('LED-HB-150W', 'IndustrialPro', 'LED High Bay', 150, 19500, 165.00, 'Heavy duty high bay, IP65 rated');
