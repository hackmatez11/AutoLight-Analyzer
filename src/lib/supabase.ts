import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  throw new Error('Missing Supabase environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey);

export interface Project {
  id: string;
  name: string;
  file_name: string;
  file_type: string;
  upload_date: string;
  total_fixtures: number;
  total_cost: number;
  average_lux: number;
  user_id: string;
  created_at: string;
}

export interface FixtureModel {
  id: string;
  model_name: string;
  manufacturer: string;
  fixture_type: string;
  wattage: number;
  lumens: number;
  unit_price: number;
  description: string;
  created_at: string;
}

export interface Fixture {
  id: string;
  project_id: string;
  room_name: string;
  detected_symbol: string;
  selected_model_id: string;
  quantity: number;
  lux_level: number;
  created_at: string;
  selected_model?: FixtureModel;
}

export interface FixtureRecommendation {
  id: string;
  fixture_id: string;
  recommended_model_id: string;
  reason: string;
  priority: number;
  created_at: string;
  recommended_model?: FixtureModel;
}
