--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alerts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.alerts (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    barangay character varying(100) NOT NULL,
    emergency_type character varying(100) NOT NULL,
    lat real NOT NULL,
    lon real NOT NULL,
    "timestamp" character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    image character varying(255)
);


ALTER TABLE public.alerts OWNER TO postgres;

--
-- Name: alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.alerts_id_seq OWNER TO postgres;

--
-- Name: alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.alerts_id_seq OWNED BY public.alerts.id;


--
-- Name: barangay_crime_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.barangay_crime_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    crime_type character varying(100) DEFAULT 'Unknown'::character varying,
    weapon_used character varying(100) DEFAULT 'Unknown'::character varying,
    time_of_day character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.barangay_crime_response OWNER TO postgres;

--
-- Name: barangay_crime_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.barangay_crime_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.barangay_crime_response_id_seq OWNER TO postgres;

--
-- Name: barangay_crime_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.barangay_crime_response_id_seq OWNED BY public.barangay_crime_response.id;


--
-- Name: barangay_fire_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.barangay_fire_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    fire_cause character varying(100) DEFAULT 'Unknown'::character varying,
    fire_type character varying(100) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    building_type character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.barangay_fire_response OWNER TO postgres;

--
-- Name: barangay_fire_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.barangay_fire_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.barangay_fire_response_id_seq OWNER TO postgres;

--
-- Name: barangay_fire_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.barangay_fire_response_id_seq OWNED BY public.barangay_fire_response.id;


--
-- Name: barangay_health_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.barangay_health_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    health_type character varying(100) DEFAULT 'Unknown'::character varying,
    health_cause character varying(100) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    patient_age integer DEFAULT 0,
    patient_gender character varying(20) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.barangay_health_response OWNER TO postgres;

--
-- Name: barangay_health_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.barangay_health_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.barangay_health_response_id_seq OWNER TO postgres;

--
-- Name: barangay_health_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.barangay_health_response_id_seq OWNED BY public.barangay_health_response.id;


--
-- Name: barangay_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.barangay_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    road_accident_cause character varying(100) DEFAULT 'Unknown'::character varying,
    road_accident_type character varying(100) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    road_condition character varying(50) DEFAULT 'Unknown'::character varying,
    vehicle_type character varying(50) DEFAULT 'Unknown'::character varying,
    driver_age integer DEFAULT 0,
    driver_gender character varying(20) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.barangay_response OWNER TO postgres;

--
-- Name: barangay_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.barangay_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.barangay_response_id_seq OWNER TO postgres;

--
-- Name: barangay_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.barangay_response_id_seq OWNED BY public.barangay_response.id;


--
-- Name: bfp_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.bfp_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    fire_cause character varying(100) DEFAULT 'Unknown'::character varying,
    fire_type character varying(100) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    building_type character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.bfp_response OWNER TO postgres;

--
-- Name: bfp_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.bfp_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.bfp_response_id_seq OWNER TO postgres;

--
-- Name: bfp_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.bfp_response_id_seq OWNED BY public.bfp_response.id;


--
-- Name: cdrrmo_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cdrrmo_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    disaster_type character varying(100) DEFAULT 'Unknown'::character varying,
    severity character varying(50) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.cdrrmo_response OWNER TO postgres;

--
-- Name: cdrrmo_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cdrrmo_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cdrrmo_response_id_seq OWNER TO postgres;

--
-- Name: cdrrmo_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cdrrmo_response_id_seq OWNED BY public.cdrrmo_response.id;


--
-- Name: health_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.health_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    health_type character varying(100) DEFAULT 'Unknown'::character varying,
    health_cause character varying(100) DEFAULT 'Unknown'::character varying,
    patient_age integer DEFAULT 0,
    patient_gender character varying(20) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.health_response OWNER TO postgres;

--
-- Name: health_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.health_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.health_response_id_seq OWNER TO postgres;

--
-- Name: health_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.health_response_id_seq OWNED BY public.health_response.id;


--
-- Name: helth_responses; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.helth_responses (
    alert_id character varying(36) NOT NULL,
    barangay character varying(100) NOT NULL,
    emergency_type character varying(100) NOT NULL,
    lat real NOT NULL,
    lon real NOT NULL,
    "timestamp" character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    image character varying(255)
);


ALTER TABLE public.helth_responses OWNER TO postgres;

--
-- Name: hospital_alerts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hospital_alerts (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    barangay character varying(100) NOT NULL,
    assigned_hospital character varying(100) NOT NULL,
    health_type character varying(100) DEFAULT 'N/A'::character varying,
    health_cause character varying(100) DEFAULT 'N/A'::character varying,
    patient_age character varying(20) DEFAULT 'N/A'::character varying,
    patient_gender character varying(20) DEFAULT 'N/A'::character varying,
    "timestamp" character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    lat real,
    lon real,
    image character varying(255)
);


ALTER TABLE public.hospital_alerts OWNER TO postgres;

--
-- Name: hospital_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hospital_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hospital_alerts_id_seq OWNER TO postgres;

--
-- Name: hospital_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hospital_alerts_id_seq OWNED BY public.hospital_alerts.id;


--
-- Name: hospital_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.hospital_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    barangay character varying(100) NOT NULL,
    assigned_hospital character varying(100) NOT NULL,
    health_type character varying(100) DEFAULT 'Unknown'::character varying,
    health_cause character varying(100) DEFAULT 'Unknown'::character varying,
    patient_age integer DEFAULT 0,
    patient_gender character varying(20) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.hospital_response OWNER TO postgres;

--
-- Name: hospital_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.hospital_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.hospital_response_id_seq OWNER TO postgres;

--
-- Name: hospital_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.hospital_response_id_seq OWNED BY public.hospital_response.id;


--
-- Name: pnp_alerts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pnp_alerts (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    barangay character varying(100) NOT NULL,
    crime_type character varying(100) DEFAULT 'N/A'::character varying,
    weapon_used character varying(100) DEFAULT 'N/A'::character varying,
    time_of_day character varying(50) DEFAULT 'N/A'::character varying,
    lat real,
    lon real,
    "timestamp" character varying(50) NOT NULL,
    status character varying(50) NOT NULL,
    image character varying(255)
);


ALTER TABLE public.pnp_alerts OWNER TO postgres;

--
-- Name: pnp_alerts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pnp_alerts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pnp_alerts_id_seq OWNER TO postgres;

--
-- Name: pnp_alerts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pnp_alerts_id_seq OWNED BY public.pnp_alerts.id;


--
-- Name: pnp_crime_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pnp_crime_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    crime_type character varying(100) DEFAULT 'Unknown'::character varying,
    weapon_used character varying(100) DEFAULT 'Unknown'::character varying,
    time_of_day character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.pnp_crime_response OWNER TO postgres;

--
-- Name: pnp_crime_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pnp_crime_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pnp_crime_response_id_seq OWNER TO postgres;

--
-- Name: pnp_crime_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pnp_crime_response_id_seq OWNED BY public.pnp_crime_response.id;


--
-- Name: pnp_fire_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pnp_fire_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    fire_cause character varying(100) DEFAULT 'Unknown'::character varying,
    fire_type character varying(100) DEFAULT 'Unknown'::character varying,
    weather character varying(50) DEFAULT 'Unknown'::character varying,
    building_type character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.pnp_fire_response OWNER TO postgres;

--
-- Name: pnp_fire_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pnp_fire_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pnp_fire_response_id_seq OWNER TO postgres;

--
-- Name: pnp_fire_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pnp_fire_response_id_seq OWNED BY public.pnp_fire_response.id;


--
-- Name: pnp_response; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pnp_response (
    id integer NOT NULL,
    alert_id character varying(36) NOT NULL,
    crime_type character varying(100) DEFAULT 'Unknown'::character varying,
    weapon_used character varying(100) DEFAULT 'Unknown'::character varying,
    time_of_day character varying(50) DEFAULT 'Unknown'::character varying,
    lat real DEFAULT 0.0,
    lon real DEFAULT 0.0,
    barangay character varying(100) DEFAULT 'Unknown'::character varying,
    emergency_type character varying(100) DEFAULT 'Unknown'::character varying,
    "timestamp" character varying(50) NOT NULL,
    responded boolean DEFAULT true
);


ALTER TABLE public.pnp_response OWNER TO postgres;

--
-- Name: pnp_response_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.pnp_response_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.pnp_response_id_seq OWNER TO postgres;

--
-- Name: pnp_response_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.pnp_response_id_seq OWNED BY public.pnp_response.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    barangay character varying(100),
    role character varying(50) NOT NULL,
    contact_no character varying(20) NOT NULL,
    assigned_municipality character varying(100),
    province character varying(100),
    password character varying(255) NOT NULL,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['resident'::character varying, 'barangay'::character varying, 'cdrrmo'::character varying, 'pnp'::character varying, 'bfp'::character varying, 'health'::character varying, 'hospital'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: alerts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alerts ALTER COLUMN id SET DEFAULT nextval('public.alerts_id_seq'::regclass);


--
-- Name: barangay_crime_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_crime_response ALTER COLUMN id SET DEFAULT nextval('public.barangay_crime_response_id_seq'::regclass);


--
-- Name: barangay_fire_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_fire_response ALTER COLUMN id SET DEFAULT nextval('public.barangay_fire_response_id_seq'::regclass);


--
-- Name: barangay_health_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_health_response ALTER COLUMN id SET DEFAULT nextval('public.barangay_health_response_id_seq'::regclass);


--
-- Name: barangay_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_response ALTER COLUMN id SET DEFAULT nextval('public.barangay_response_id_seq'::regclass);


--
-- Name: bfp_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bfp_response ALTER COLUMN id SET DEFAULT nextval('public.bfp_response_id_seq'::regclass);


--
-- Name: cdrrmo_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cdrrmo_response ALTER COLUMN id SET DEFAULT nextval('public.cdrrmo_response_id_seq'::regclass);


--
-- Name: health_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.health_response ALTER COLUMN id SET DEFAULT nextval('public.health_response_id_seq'::regclass);


--
-- Name: hospital_alerts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hospital_alerts ALTER COLUMN id SET DEFAULT nextval('public.hospital_alerts_id_seq'::regclass);


--
-- Name: hospital_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hospital_response ALTER COLUMN id SET DEFAULT nextval('public.hospital_response_id_seq'::regclass);


--
-- Name: pnp_alerts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_alerts ALTER COLUMN id SET DEFAULT nextval('public.pnp_alerts_id_seq'::regclass);


--
-- Name: pnp_crime_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_crime_response ALTER COLUMN id SET DEFAULT nextval('public.pnp_crime_response_id_seq'::regclass);


--
-- Name: pnp_fire_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_fire_response ALTER COLUMN id SET DEFAULT nextval('public.pnp_fire_response_id_seq'::regclass);


--
-- Name: pnp_response id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_response ALTER COLUMN id SET DEFAULT nextval('public.pnp_response_id_seq'::regclass);


--
-- Data for Name: alerts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.alerts (id, alert_id, barangay, emergency_type, lat, lon, "timestamp", status, image) FROM stdin;
\.


--
-- Data for Name: barangay_crime_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.barangay_crime_response (id, alert_id, crime_type, weapon_used, time_of_day, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: barangay_fire_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.barangay_fire_response (id, alert_id, fire_cause, fire_type, weather, building_type, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: barangay_health_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.barangay_health_response (id, alert_id, health_type, health_cause, weather, patient_age, patient_gender, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: barangay_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.barangay_response (id, alert_id, road_accident_cause, road_accident_type, weather, road_condition, vehicle_type, driver_age, driver_gender, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: bfp_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.bfp_response (id, alert_id, fire_cause, fire_type, weather, building_type, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: cdrrmo_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cdrrmo_response (id, alert_id, disaster_type, severity, weather, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: health_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.health_response (id, alert_id, health_type, health_cause, patient_age, patient_gender, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: helth_responses; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.helth_responses (alert_id, barangay, emergency_type, lat, lon, "timestamp", status, image) FROM stdin;
\.


--
-- Data for Name: hospital_alerts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.hospital_alerts (id, alert_id, barangay, assigned_hospital, health_type, health_cause, patient_age, patient_gender, "timestamp", status, lat, lon, image) FROM stdin;
\.


--
-- Data for Name: hospital_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.hospital_response (id, alert_id, barangay, assigned_hospital, health_type, health_cause, patient_age, patient_gender, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: pnp_alerts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pnp_alerts (id, alert_id, barangay, crime_type, weapon_used, time_of_day, lat, lon, "timestamp", status, image) FROM stdin;
\.


--
-- Data for Name: pnp_crime_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pnp_crime_response (id, alert_id, crime_type, weapon_used, time_of_day, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: pnp_fire_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pnp_fire_response (id, alert_id, fire_cause, fire_type, weather, building_type, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: pnp_response; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pnp_response (id, alert_id, crime_type, weapon_used, time_of_day, lat, lon, barangay, emergency_type, "timestamp", responded) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (barangay, role, contact_no, assigned_municipality, province, password) FROM stdin;
\.


--
-- Name: alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.alerts_id_seq', 1, false);


--
-- Name: barangay_crime_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.barangay_crime_response_id_seq', 1, false);


--
-- Name: barangay_fire_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.barangay_fire_response_id_seq', 1, false);


--
-- Name: barangay_health_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.barangay_health_response_id_seq', 1, false);


--
-- Name: barangay_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.barangay_response_id_seq', 1, false);


--
-- Name: bfp_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.bfp_response_id_seq', 1, false);


--
-- Name: cdrrmo_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cdrrmo_response_id_seq', 1, false);


--
-- Name: health_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.health_response_id_seq', 1, false);


--
-- Name: hospital_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.hospital_alerts_id_seq', 1, false);


--
-- Name: hospital_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.hospital_response_id_seq', 1, false);


--
-- Name: pnp_alerts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pnp_alerts_id_seq', 1, false);


--
-- Name: pnp_crime_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pnp_crime_response_id_seq', 1, false);


--
-- Name: pnp_fire_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pnp_fire_response_id_seq', 1, false);


--
-- Name: pnp_response_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.pnp_response_id_seq', 1, false);


--
-- Name: alerts alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.alerts
    ADD CONSTRAINT alerts_pkey PRIMARY KEY (alert_id, barangay);


--
-- Name: barangay_crime_response barangay_crime_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_crime_response
    ADD CONSTRAINT barangay_crime_response_pkey PRIMARY KEY (id);


--
-- Name: barangay_fire_response barangay_fire_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_fire_response
    ADD CONSTRAINT barangay_fire_response_pkey PRIMARY KEY (id);


--
-- Name: barangay_health_response barangay_health_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_health_response
    ADD CONSTRAINT barangay_health_response_pkey PRIMARY KEY (id);


--
-- Name: barangay_response barangay_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.barangay_response
    ADD CONSTRAINT barangay_response_pkey PRIMARY KEY (id);


--
-- Name: bfp_response bfp_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.bfp_response
    ADD CONSTRAINT bfp_response_pkey PRIMARY KEY (id);


--
-- Name: cdrrmo_response cdrrmo_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cdrrmo_response
    ADD CONSTRAINT cdrrmo_response_pkey PRIMARY KEY (id);


--
-- Name: health_response health_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.health_response
    ADD CONSTRAINT health_response_pkey PRIMARY KEY (id);


--
-- Name: helth_responses helth_responses_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.helth_responses
    ADD CONSTRAINT helth_responses_pkey PRIMARY KEY (alert_id);


--
-- Name: hospital_alerts hospital_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hospital_alerts
    ADD CONSTRAINT hospital_alerts_pkey PRIMARY KEY (id);


--
-- Name: hospital_response hospital_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hospital_response
    ADD CONSTRAINT hospital_response_pkey PRIMARY KEY (id);


--
-- Name: pnp_alerts pnp_alerts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_alerts
    ADD CONSTRAINT pnp_alerts_pkey PRIMARY KEY (id);


--
-- Name: pnp_crime_response pnp_crime_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_crime_response
    ADD CONSTRAINT pnp_crime_response_pkey PRIMARY KEY (id);


--
-- Name: pnp_fire_response pnp_fire_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_fire_response
    ADD CONSTRAINT pnp_fire_response_pkey PRIMARY KEY (id);


--
-- Name: pnp_response pnp_response_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_response
    ADD CONSTRAINT pnp_response_pkey PRIMARY KEY (id);


--
-- Name: users users_contact_no_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_contact_no_key UNIQUE (contact_no);


--
-- Name: hospital_alerts fk_alerts; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.hospital_alerts
    ADD CONSTRAINT fk_alerts FOREIGN KEY (alert_id, barangay) REFERENCES public.alerts(alert_id, barangay);


--
-- Name: pnp_alerts fk_alerts; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pnp_alerts
    ADD CONSTRAINT fk_alerts FOREIGN KEY (alert_id, barangay) REFERENCES public.alerts(alert_id, barangay);


--
-- PostgreSQL database dump complete
--

