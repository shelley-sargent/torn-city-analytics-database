-- ========================
-- Tornbot Database Schema
-- ========================

-- Players table (static/semi-static player info)
CREATE TABLE public.players (
    player_id integer NOT NULL,
    torn_name text,
    discord_id text,
    discord_name text,
    api_key text,
    faction_id integer,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now(),
    CONSTRAINT players_pkey PRIMARY KEY (player_id),
    CONSTRAINT players_discord_id_key UNIQUE (discord_id)
);

-- Attacks table (denormalized, one row per attack, used for ML/analysis)
CREATE TABLE public.attacks (
    id text NOT NULL,
    started timestamp with time zone,
    ended timestamp with time zone,
    attacker_id integer,
    attacker_faction_id integer,
    defender_id integer,
    defender_faction_id integer,
    result text,
    respect_gain numeric,
    respect_loss numeric,
    code text,
    attacker_elo numeric,
    attacker_revives bigint,
    attacker_refills bigint,
    attacker_networth bigint,
    attacker_boostersused bigint,
    attacker_attackcriticalhits bigint,
    attacker_cantaken bigint,
    attacker_xantaken bigint,
    attacker_bestdamage bigint,
    attacker_statenhancersused bigint,
    defender_elo numeric,
    defender_revives bigint,
    defender_refills bigint,
    defender_networth bigint,
    defender_boostersused bigint,
    defender_attackcriticalhits bigint,
    defender_cantaken bigint,
    defender_xantaken bigint,
    defender_bestdamage bigint,
    defender_statenhancersused bigint,
    CONSTRAINT attacks_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_attacks_attacker ON public.attacks USING btree (attacker_id);
CREATE INDEX idx_attacks_defender ON public.attacks USING btree (defender_id);

-- Player stats daily (hourly snapshots of cumulative player stats)
CREATE TABLE public.player_stats_daily (
    id bigint NOT NULL,
    player_id integer NOT NULL,
    snapshot_date timestamp with time zone NOT NULL,
    torn_name text,
    elo numeric,
    respectforfaction numeric,
    refills integer,
    nerverefills integer,
    activestreak integer,
    hospital integer,
    jailed integer,
    attackswon integer,
    attackslost integer,
    attacksdraw integer,
    attacksassisted integer,
    defendswon integer,
    defendslost integer,
    defendsstalemated integer,
    yourunaway integer,
    theyrunaway integer,
    attackhits integer,
    attackmisses integer,
    bestdamage integer,
    onehitkills integer,
    attackcriticalhits integer,
    bestkillstreak integer,
    retals integer,
    itemslooted integer,
    rankedwarhits integer,
    raidhits integer,
    xantaken integer,
    cantaken integer,
    victaken integer,
    drugsused integer,
    overdosed integer,
    boostersused integer,
    energydrinkused integer,
    statenhancersused integer,
    gymtrains integer,
    networth bigint,
    attackdamage bigint,
    moneymugged bigint,
    largestmug bigint,
    timeplayed bigint,
    gymenergy bigint,
    gymstrength bigint,
    gymdefense bigint,
    gymdexterity bigint,
    gymspeed bigint,
    territoryrespect bigint,
    CONSTRAINT player_stats_daily_pkey PRIMARY KEY (id),
    CONSTRAINT player_stats_daily_player_id_snapshot_date_key UNIQUE (player_id, snapshot_date)
);

CREATE SEQUENCE public.player_stats_daily_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.player_stats_daily_id_seq OWNED BY public.player_stats_daily.id;
ALTER TABLE ONLY public.player_stats_daily ALTER COLUMN id SET DEFAULT nextval('public.player_stats_daily_id_seq'::regclass);

CREATE INDEX idx_psd_player_date ON public.player_stats_daily USING btree (player_id, snapshot_date DESC);

-- Ranked war attacks table (all attacks during an active ranked war)
CREATE TABLE public.ranked_war_attacks (
    id                    text NOT NULL,
    war_id                integer NOT NULL,
    code                  text,
    started               timestamp with time zone,
    ended                 timestamp with time zone,
    attacker_id           integer,
    attacker_name         text,
    attacker_level        integer,
    attacker_faction_id   integer,
    attacker_faction      text,
    defender_id           integer,
    defender_name         text,
    defender_level        integer,
    defender_faction_id   integer,
    defender_faction      text,
    result                text,
    respect_gain          numeric,
    respect_loss          numeric,
    chain                 integer,
    is_interrupted        boolean,
    is_stealthed          boolean,
    is_raid               boolean,
    is_ranked_war         boolean,
    mod_fair_fight        numeric,
    mod_war               numeric,
    mod_retaliation       numeric,
    mod_group             numeric,
    mod_overseas          numeric,
    mod_chain             numeric,
    mod_warlord           numeric,
    finishing_hit_effects jsonb,
    CONSTRAINT ranked_war_attacks_pkey PRIMARY KEY (id)
);

CREATE INDEX idx_rwa_war_id ON public.ranked_war_attacks USING btree (war_id);
CREATE INDEX idx_rwa_attacker ON public.ranked_war_attacks USING btree (attacker_id);
CREATE INDEX idx_rwa_defender ON public.ranked_war_attacks USING btree (defender_id);

-- ========================
-- Permissions
-- ========================
GRANT ALL ON TABLE public.attacks TO tornbot_user;
GRANT ALL ON TABLE public.player_stats_daily TO tornbot_user;
GRANT ALL ON TABLE public.players TO tornbot_user;
GRANT ALL ON TABLE public.ranked_war_attacks TO tornbot_user;
GRANT SELECT, USAGE ON SEQUENCE public.player_stats_daily_id_seq TO tornbot_user;
