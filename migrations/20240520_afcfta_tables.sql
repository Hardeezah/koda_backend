-- Migration to add AfCFTA tables and enable RLS

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- afcfta_tariff_schedule
CREATE TABLE IF NOT EXISTS public.afcfta_tariff_schedule (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hs_code TEXT NOT NULL,
    product_description TEXT,
    category TEXT CHECK (category IN ('liberalised','sensitive','excluded')),
    destination_country TEXT,
    current_rate_percent NUMERIC,
    afcfta_rate_percent NUMERIC,
    phase_down_end_year INTEGER,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- afcfta_roo_requirements
CREATE TABLE IF NOT EXISTS public.afcfta_roo_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hs_code_prefix TEXT NOT NULL,
    rule_type TEXT CHECK (rule_type IN ('wholly_obtained','sufficient_transformation','specific_rule')),
    rule_description TEXT,
    minimum_african_value_percent NUMERIC,
    requires_hs_change BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- afcfta_checks
CREATE TABLE IF NOT EXISTS public.afcfta_checks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    hs_code TEXT,
    product_description TEXT,
    destination_country TEXT,
    roo_eligible BOOLEAN,
    tariff_saving_percent NUMERIC,
    documents_required JSONB,
    roo_evidence_required JSONB,
    ai_explanation TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Enable RLS on afcfta_checks
ALTER TABLE public.afcfta_checks ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_can_read_own ON public.afcfta_checks
    FOR SELECT USING (auth.uid() = user_id);
