# Deploying BrickTracker

BrickTracker is one Render web service using Supabase Postgres and Supabase Auth. Every account has a separate collection.

## Supabase

1. In **Authentication**, open **Providers**, enable **Email**, and choose whether new accounts must confirm their email addresses.
2. In **Authentication**, open **URL Configuration**. Add the final Render URL as a redirect URL after the first deployment.
3. From the project **Get connected** page, copy the project URL and anon key. The anon key is safe to use in the browser; do not use the service-role key.
4. Keep the Session pooler connection string as `DATABASE_URL`. It must include `sslmode=require`.

The application creates its tables in Supabase during its first successful startup.

## Render

1. Push this folder to a GitHub repository.
2. In Render, select **New +**, then **Blueprint**, and connect that repository.
3. Render detects `render.yaml`. Enter these environment variables when prompted:
   - `DATABASE_URL`: the Supabase Session pooler URI
   - `SUPABASE_URL`: the project URL
   - `SUPABASE_ANON_KEY`: the Supabase anon key
   - `BRICKLINK_CONSUMER_KEY`
   - `BRICKLINK_CONSUMER_SECRET`
   - `BRICKLINK_TOKEN`
   - `BRICKLINK_TOKEN_SECRET`
4. Deploy. Render supplies an HTTPS URL that opens BrickTracker from any browser and device.

Keep `DATABASE_URL` and BrickLink credentials only in Render environment variables. Do not commit them, paste them into chat, or put them in browser code.