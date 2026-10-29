# Disable unaccounted legacy live entry points

Historical Groq and service evaluation entry points dispatch without the shared account guard; the latter may also create resources. The workflow runtime also constructs an unaccounted SDK client. Refuse both entry points before credentials, provider, service or evidence access, and refuse default runtime provider construction until an accounted integration exists. Preserve offline helpers and historical evidence.
