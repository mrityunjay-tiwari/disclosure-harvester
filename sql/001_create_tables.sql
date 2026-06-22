create table if not exists sources (
    source_id text not null,
    amc_name text not null,
    url text not null,
    source_type text not null,
    active boolean not null,
    validated_end_to_end boolean not null,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,
    unique(source_id, url)
);

create table if not exists pipeline_runs (
    run_id text primary key,
    started_at timestamp default current_timestamp,
    finished_at timestamp,
    status text not null,
    sources_checked integer default 0,
    documents_found integer default 0,
    documents_downloaded integer default 0,
    documents_skipped integer default 0,
    documents_quarantined integer default 0,
    documents_published integer default 0,
    error_message text
);

create table if not exists discovered_documents (
    document_id text primary key,
    run_id text not null,
    source_id text not null,
    page_url text not null,
    document_url text not null,
    normalized_url text not null unique,
    link_text text,
    surrounding_text text,
    file_type text not null,
    discovered_at timestamp default current_timestamp
);

create table if not exists raw_files (
    file_id text primary key,
    document_id text not null,
    storage_path text not null,
    sha256 text not null unique,
    file_size integer not null,
    mime_type text,
    downloaded_at timestamp default current_timestamp,
    is_duplicate boolean not null
);

create table if not exists document_classifications (
    classification_id text primary key,
    file_id text not null,
    amc_name text,
    period text,
    document_type text,
    confidence_score integer not null,
    status text not null,
    hard_conflict boolean not null,
    evidence_json text not null,
    created_at timestamp default current_timestamp
);

create table if not exists staging_rows (
    staging_id text primary key,
    file_id text not null,
    sheet_or_page text,
    section_name text,
    scheme_name_raw text,
    row_number integer not null,
    raw_data_json text not null,
    parser_used text not null,
    extracted_at timestamp default current_timestamp
);

create table if not exists published_holdings (
    holding_id text primary key,
    amc_name text not null,
    scheme_name text not null,
    period text not null,
    document_type text not null,
    holding_business_key text not null,
    isin text,
    security_name text not null,
    asset_type text not null,
    quantity double,
    market_value double,
    percentage_to_nav double,
    source_file_id text not null,
    source_sha256 text not null,
    is_current boolean not null,
    superseded_by_file_id text,
    published_at timestamp default current_timestamp
);

create table if not exists layout_fingerprints (
    fingerprint_id text primary key,
    source_id text not null,
    amc_name text not null,
    document_type text not null,
    scheme_name text,
    expected_headers_json text not null,
    last_good_row_count integer not null,
    last_good_confidence_avg double not null,
    last_good_page_count integer,
    last_good_file_hash text not null,
    parser_used text not null,
    updated_at timestamp default current_timestamp
);

create table if not exists quarantine (
    quarantine_id text primary key,
    file_id text,
    reason text not null,
    details_json text not null,
    confidence_score integer,
    status text not null,
    created_at timestamp default current_timestamp,
    reviewed_at timestamp,
    reviewed_by text,
    resolution_note text
);

create table if not exists audit_events (
    event_id text primary key,
    run_id text,
    file_id text,
    source_id text,
    event_type text not null,
    message text not null,
    metadata_json text not null,
    created_at timestamp default current_timestamp
);
